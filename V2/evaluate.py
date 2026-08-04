"""
평가 스크립트 — "학습이 끝난 모델이 실제로 얼마나 정확한가"를 재는 도구.
(sim2real 실행계획 Step 2의 앞부분. 2026-07-11 작성)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 이 스크립트가 필요한 이유 (초보자용 배경 설명)

  학습(train.py)이 끝나면 두 종류의 체크포인트(.pt = 모델 가중치 저장 파일)가 남는다:

    {name}.pt        : "종합 점수(val loss)"가 가장 좋았던 시점의 모델.
                       train.py가 마지막에 보정계수·[TEST] 점수까지 계산해서
                       파일 안에 같이 넣어 준다. → 이미 성적표가 있음.
    {name}_bestH.pt  : "높이(H) 하나만" 가장 잘 맞히던 시점의 모델.
                       train.py는 이 파일에는 성적표를 안 만들어 준다. ← 문제!

  우리 연구에서는 "높이 전문가"로 bestH 체크포인트를 쓰고 싶은데,
  성적표(보정 후 H_MAE, [TEST] 점수)가 없어서 좋은지 나쁜지 모른다.
  이 스크립트는 **아무 체크포인트나 받아서 성적표를 새로 만들어 준다.**

■ 용어 미니 사전
  val(검증셋)   : 학습 중 컨닝 없이 실력을 재는 문제집 (전체 데이터의 10%).
                  보정계수도 여기서 구한다 (시험지인 test를 건드리면 반칙).
  test(테스트셋): 마지막에 딱 한 번 채점하는 진짜 시험지 (10%).
  MAE           : Mean Absolute Error. |예측 − 정답| 의 평균. 작을수록 좋다.
                  H_MAE는 mm 단위 높이 오차, r_MAE는 mm 단위 반지름 오차.
  H 보정(calibration):
                  모델이 내놓는 높이가 "일정하게 눌리거나 밀려" 있을 때
                  1차 함수 (진짜 ≈ a×예측 + b) 로 눈금을 펴 주는 것.
                  검증셋에서 a, b를 구해 두면 시험지·실측에도 그대로 적용.
                  ※ 산포(들쭉날쭉함)는 못 고친다 — 눈금만 편다.

■ 사용법 (프로젝트 루트 acoustic_simulation\ 에서)
  python v2\evaluate.py --ckpt dataset\models_v2\rnn_ratio_nodetach_bestH.pt
  python v2\evaluate.py --ckpt dataset\models_v2\rnn_continuity.pt
  옵션:
    --save    : 계산한 보정계수·성적표를 체크포인트 파일 안에 다시 저장
                (combine.py가 그대로 읽어 쓸 수 있게 됨. 권장)
    --workers 4 : 데이터 로딩 병렬화(속도 ↑)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
from torch.utils.data import DataLoader

from v2 import config
from v2.data import loader
from v2.models.baseline import mae_mm
# train.py의 데이터 준비/모델 조립 코드를 그대로 재사용 —
# 학습 때와 조금이라도 다르게 만들면 점수가 왜곡되므로 "복붙"이 아니라 "임포트"한다.
from v2.train import ChunkCollate, build_datasets, build_model


# ─────────────────────────────────────────────────────────────
# 1) 체크포인트 → 모델 복원
# ─────────────────────────────────────────────────────────────
def load_model_from_ckpt(ckpt_path, device):
    """체크포인트 파일 하나에서 (모델, ckpt 딕셔너리)를 복원한다.

    체크포인트 안에는 가중치(model_state)뿐 아니라 '설계도'도 들어 있다:
      arch : 모델 종류(set/rnn), 입력 크기(n_bins), 옵션(model_kw: 방향, detach 등)
      aug  : 학습 때 쓴 전처리 설정(mode, crop_hz) — 평가 때도 똑같이 맞춰야 공정.
    """
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    arch = ckpt["arch"]
    model_kw = arch.get("model_kw") or {}
    model = build_model(arch.get("model", "set"), arch["n_bins"], **model_kw).to(device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()  # 평가 모드: dropout 끔 (안 끄면 점수가 랜덤하게 나빠짐)
    return model, ckpt


# ─────────────────────────────────────────────────────────────
# 2) 데이터셋 한 바퀴 추론 (학습 없음, 채점만)
# ─────────────────────────────────────────────────────────────
def shuffle_steps(X, V, sm, rng):
    """셔플 테스트(어블레이션 A1)용: 각 샘플의 유효 스텝 구간을
    (스펙트럼, 부피) '쌍 단위'로 무작위 재배열한다.

    쌍을 함께 섞으므로 '스텝들의 집합'으로서의 정보는 그대로이고,
    파괴되는 것은 오직 '제시 순서(시간 구조)'뿐이다.
    → set 모델(풀링)은 점수가 변하지 않아야 정상(불변성 검증),
      RNN의 점수 악화량 = 순서 정보의 기여량."""
    X = X.clone(); V = V.clone()
    lengths = sm.sum(1).long()
    for i in range(X.size(0)):
        L = int(lengths[i])
        if L > 1:
            perm = torch.from_numpy(rng.permutation(L))
            X[i, :L] = X[i, perm]
            V[i, :L] = V[i, perm]
    return X, V


@torch.no_grad()  # 기울기 계산 끔 → 메모리·속도 이득 (채점에는 학습이 필요 없다)
def run_inference(model, dl, device, shuffle_rng=None):
    """데이터로더 전체에 대해 예측을 모은다.
    shuffle_rng를 주면 배치마다 스텝 순서를 셔플해서 넣는다(셔플 테스트).
    반환: (H예측, H정답, r예측, r정답, r마스크) — 전부 정규화(0~1) 단위 numpy."""
    ph_all, yh_all, pr_all, yr_all, lm_all = [], [], [], [], []
    for X, V, sm, yh, yr, lm, _stop in dl:
        if shuffle_rng is not None:
            X, V = shuffle_steps(X, V, sm, shuffle_rng)
        X, V, sm = X.to(device), V.to(device), sm.to(device)
        ph, pr = model(X, V, sm)
        ph_all.append(ph.cpu()); yh_all.append(yh)
        pr_all.append(pr.cpu()); yr_all.append(yr); lm_all.append(lm)
    return (torch.cat(ph_all).numpy(), torch.cat(yh_all).numpy(),
            torch.cat(pr_all).numpy(), torch.cat(yr_all).numpy(),
            torch.cat(lm_all).numpy())


# ─────────────────────────────────────────────────────────────
# 3) 점수 계산 유틸
# ─────────────────────────────────────────────────────────────
H_SCALE_MM = (config.H_MAX - config.H_MIN) * 1000  # 정규화 H 1.0 = 220mm
R_SCALE_MM = (config.R_MAX - config.R_MIN) * 1000  # 정규화 r 1.0 = 45mm


def fit_h_calibration(pred_h, true_h):
    """검증셋에서 H 보정 1차식 적합: true ≈ a·pred + b.
    train.py의 [CALIB]와 완전히 같은 방법 (np.polyfit 1차)."""
    a, b = np.polyfit(pred_h, true_h, 1)
    return float(a), float(b)


def h_mae_mm(pred_h, true_h, calib=None):
    """H MAE를 mm로. calib=(a,b)를 주면 보정 후 점수."""
    if calib is not None:
        a, b = calib
        pred_h = a * pred_h + b
    return float(np.abs(pred_h - true_h).mean() * H_SCALE_MM)


def r_mae_mm_overall(pred_r, true_r, l_mask):
    """전체 슬롯 평균 r MAE (mm). 유효 슬롯(l_mask=1)만 채점."""
    return float((np.abs(pred_r - true_r) * l_mask).sum() / max(l_mask.sum(), 1.0)
                 * R_SCALE_MM)


def r_mae_mm_per_slot(pred_r, true_r, l_mask):
    """슬롯별 r MAE (mm) 표.

    슬롯 = 컵을 바닥부터 10mm 간격으로 자른 25개 층.
    높은 슬롯(컵 위쪽)은 '키 큰 컵'에만 존재하므로 샘플 수가 적다 →
    슬롯마다 유효 샘플 수(count)도 같이 보여 준다.
    반환: [(슬롯번호, 시작mm, 끝mm, 샘플수, MAE_mm), ...]"""
    err = np.abs(pred_r - true_r) * l_mask                 # (N, 25)
    cnt = l_mask.sum(axis=0)                               # 슬롯별 유효 샘플 수
    mae = err.sum(axis=0) / np.maximum(cnt, 1.0) * R_SCALE_MM
    rows = []
    for s in range(config.N_SLOTS):
        lo = s * config.SLOT_PITCH * 1000
        rows.append((s, lo, lo + config.SLOT_PITCH * 1000, int(cnt[s]), float(mae[s])))
    return rows


# ─────────────────────────────────────────────────────────────
# 4) 메인: 체크포인트 하나 완전 채점
# ─────────────────────────────────────────────────────────────
def evaluate_checkpoint(ckpt_path, data_dir="dataset/v2", batch=64,
                        workers=0, device=None, save=False, max_samples=None,
                        shuffle=False):
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model, ckpt = load_model_from_ckpt(ckpt_path, device)

    # ── 학습 때와 동일한 전처리·분할 재구성 ──────────────────
    aug = ckpt["aug"]
    aug_cfg = loader.AugmentConfig(mode=aug["mode"], crop_hz=aug["crop_hz"])

    # 분할 시드: 메인 체크포인트에는 split 정보가 저장돼 있고,
    # bestH 체크포인트에는 없다 → 없으면 train.py 기본값(seed 42)으로 재구성.
    # (같은 데이터 폴더 + 같은 시드 = 같은 분할이 보장됨: numpy 시드 고정 순열)
    split = ckpt.get("split") or {}
    split_seed = split.get("seed", 42)
    if max_samples is None:
        max_samples = split.get("max_samples")

    store, idx, _, ds_va, ds_te, collate = build_datasets(
        data_dir, aug_cfg, max_samples, split_seed=split_seed)

    # 안전장치: 저장된 test 인덱스가 있으면 재구성 결과와 대조.
    # 어긋나면 = 데이터 폴더가 학습 때와 다르다는 뜻 → 점수를 믿으면 안 됨.
    if "test_idx" in split:
        saved = set(split["test_idx"])
        rebuilt = set(idx["test"].tolist())
        if saved != rebuilt:
            print("[경고] 저장된 test 분할과 재구성 분할이 다릅니다! "
                  "데이터 폴더/샘플 수가 학습 때와 다른 듯 — 결과 신뢰 불가.")

    dl_va = DataLoader(ds_va, batch_size=batch, shuffle=False,
                       collate_fn=collate, num_workers=workers)
    dl_te = DataLoader(ds_te, batch_size=batch, shuffle=False,
                       collate_fn=collate, num_workers=workers)

    name = os.path.basename(ckpt_path)
    print(f"\n{'=' * 62}\n채점: {name}  (model={ckpt['arch'].get('model')}, "
          f"epoch={ckpt.get('epoch', '?')}, device={device})\n{'=' * 62}")
    if shuffle:
        if save:
            print("[주의] --shuffle 점수는 진단용이라 --save를 무시합니다 "
                  "(체크포인트 성적표 오염 방지).")
            save = False
        print("[SHUFFLE] 스텝 순서 셔플 모드 — (스펙트럼, V) 쌍 단위로 재배열, "
              "시드 123 고정.")
    sh_rng = np.random.default_rng(123) if shuffle else None

    # ── ① 검증셋: 보정계수 적합 ─────────────────────────────
    vp_h, vt_h, vp_r, vt_r, v_lm = run_inference(model, dl_va, device, sh_rng)
    calib = fit_h_calibration(vp_h, vt_h)
    print(f"[CALIB] H 보정식: true ≈ {calib[0]:.3f}·pred + {calib[1]:.3f}  (val 적합)")
    print(f"[VAL ] H_MAE raw {h_mae_mm(vp_h, vt_h):6.2f}mm → 보정 후 "
          f"{h_mae_mm(vp_h, vt_h, calib):6.2f}mm | r_MAE "
          f"{r_mae_mm_overall(vp_r, vt_r, v_lm):5.2f}mm")

    # ── ② 테스트셋: 최종 성적표 ─────────────────────────────
    tp_h, tt_h, tp_r, tt_r, t_lm = run_inference(model, dl_te, device, sh_rng)
    h_raw = h_mae_mm(tp_h, tt_h)
    h_cal = h_mae_mm(tp_h, tt_h, calib)
    r_all = r_mae_mm_overall(tp_r, tt_r, t_lm)
    print(f"[TEST] H_MAE raw {h_raw:6.2f}mm → 보정 후 {h_cal:6.2f}mm "
          f"| r_MAE {r_all:5.2f}mm  (샘플 {len(tp_h)}개)")

    print("\n[TEST] 슬롯별 r_MAE  (슬롯 = 바닥부터 10mm 층):")
    print("  슬롯   구간(mm)    샘플수   MAE(mm)")
    for s, lo, hi, cnt, mae in r_mae_mm_per_slot(tp_r, tt_r, t_lm):
        bar = "#" * min(int(round(mae * 4)), 60)  # 시각화 막대 (1# = 0.25mm, 최대 60)
        print(f"  {s:3d}  {lo:4.0f}~{hi:4.0f}   {cnt:6d}   {mae:6.2f}  {bar}")

    # ── ③ (옵션) 성적표를 체크포인트에 저장 ──────────────────
    if save:
        ckpt["calib_h"] = {"a": calib[0], "b": calib[1]}
        ckpt["test_metrics"] = {"H_MAE_mm": h_raw, "H_MAE_calibrated_mm": h_cal,
                                "r_MAE_mm": r_all}
        torch.save(ckpt, ckpt_path)
        print(f"\n[SAVED] 보정계수·성적표를 {ckpt_path} 안에 저장했습니다. "
              f"(combine.py가 자동으로 사용)")

    return {"H_MAE_mm": h_raw, "H_MAE_calibrated_mm": h_cal, "r_MAE_mm": r_all,
            "calib_h": {"a": calib[0], "b": calib[1]}}


def main():
    ap = argparse.ArgumentParser(description="체크포인트 채점기 (보정 후 TEST + 슬롯별 r_MAE)")
    ap.add_argument("--ckpt", required=True, help="채점할 .pt 파일 경로")
    ap.add_argument("--data", default="dataset/v2")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--device", default=None)
    ap.add_argument("--samples", type=int, default=None,
                    help="(디버그용) 데이터 일부만 사용 — 분할이 달라지므로 점수는 참고용")
    ap.add_argument("--save", action="store_true",
                    help="보정계수와 성적표를 체크포인트 파일에 기록")
    ap.add_argument("--shuffle", action="store_true",
                    help="셔플 테스트(어블레이션 A1): 스텝 순서를 무작위 재배열해 채점. "
                         "RNN의 악화량 = 순서 정보의 기여. set 모델은 불변이어야 정상.")
    a = ap.parse_args()
    evaluate_checkpoint(a.ckpt, a.data, a.batch, a.workers, a.device,
                        save=a.save, max_samples=a.samples, shuffle=a.shuffle)


if __name__ == "__main__":
    main()
