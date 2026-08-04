"""
결합 추론 유틸 — "전문가 두 명"을 한 팀으로 묶는 도구.
(sim2real 실행계획 Step 2의 뒷부분. 2026-07-11 작성)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 왜 두 모델을 결합하나? (초보자용 배경 설명)

  우리 모델은 한 번에 두 가지를 맞혀야 한다:
    H     = 컵(공동)의 전체 높이 1개
    r(z)  = 바닥부터 10mm 층마다의 반지름 25개

  그런데 한 모델 안에서 두 과제가 몸통(trunk)을 공유하면
  서로 gradient(학습 신호)를 뺏는 "시소" 현상이 생긴다 —
  반지름이 좋아지면 높이가 나빠지고, 그 반대도 마찬가지.
  (지금까지 실험 로그가 전부 이 패턴이었다.)

  해결: 아예 모델을 두 개 쓰고 잘하는 것만 시킨다.
    H 전문가  : 높이만 믿고 가져온다 (+ 1차식 보정 적용)
    r 전문가  : 반지름 프로파일만 가져온다 (continuity 학습 모델)
  → 시소의 근원(몸통 공유) 자체가 사라진다.

  남는 약점: 두 예측이 서로 물리적으로 안 맞을 수 있음
  (예: H 전문가는 "17cm 컵", r 전문가의 부피는 "20cm 컵" 느낌).
  → 이것은 다음 단계인 "테스트타임 정제"(tmm_torch.py 참고)가 봉합한다.

■ 사용법 (프로젝트 루트 acoustic_simulation\ 에서)

  1) 시뮬 테스트셋 채점 (전문가 결합이 단일 모델보다 나은지 확인):
     python v2\combine.py --h_ckpt dataset\models_v2\rnn_ratio_nodetach_bestH.pt ^
                          --r_ckpt dataset\models_v2\rnn_continuity.pt

  2) 파이썬에서 실측 데이터 1개 추론 (나중에 링 실측 검증 때):
     from v2.combine import CombinedPredictor
     cp = CombinedPredictor("...h.pt", "...r.pt")
     H_mm, r_mm = cp.predict(spec_seq, v_seq)   # 물리 단위(mm)로 반환

  ※ H 전문가 체크포인트에 보정계수가 없으면(bestH 파일이 그렇다)
    검증셋에서 즉석으로 구한다. 미리 evaluate.py --save 를 돌려 두면
    저장된 보정계수를 그대로 읽어서 더 빠르다.
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
from v2.evaluate import (H_SCALE_MM, R_SCALE_MM, fit_h_calibration, h_mae_mm,
                         load_model_from_ckpt, r_mae_mm_overall,
                         r_mae_mm_per_slot, run_inference)
from v2.train import build_datasets


# ─────────────────────────────────────────────────────────────
# 결합 예측기
# ─────────────────────────────────────────────────────────────
class CombinedPredictor:
    """H 전문가 + r 전문가를 묶은 예측기.

    predict() 하나로 (H[mm], r(z)[mm] 25개)를 돌려준다.
    나중에 실측 스펙트럼에도 그대로 쓸 수 있게 전처리를 내장했다."""

    def __init__(self, h_ckpt_path, r_ckpt_path, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.h_model, self.h_ckpt = load_model_from_ckpt(h_ckpt_path, self.device)
        self.r_model, self.r_ckpt = load_model_from_ckpt(r_ckpt_path, self.device)

        # 두 전문가의 전처리 설정(모드·주파수 crop)이 같아야 같은 입력을 먹일 수 있다.
        ah, ar = self.h_ckpt["aug"], self.r_ckpt["aug"]
        if (ah["mode"], ah["crop_hz"]) != (ar["mode"], ar["crop_hz"]):
            raise ValueError(f"전처리 불일치: H 전문가 {ah} vs r 전문가 {ar} — "
                             "같은 mode/crop으로 학습된 체크포인트를 쓰세요.")
        self.aug = ah

        # H 보정계수: 체크포인트에 있으면 사용, 없으면 None(호출부에서 적합).
        cal = self.h_ckpt.get("calib_h")
        self.calib = (cal["a"], cal["b"]) if cal else None

        # 실측 추론용 전처리 설정: 증강(enabled=False) 없이
        # crop → 시퀀스 z-score → V 정규화만 수행 (학습 §6 전처리와 동일).
        self.pre_cfg = loader.AugmentConfig(mode=self.aug["mode"],
                                            crop_hz=self.aug["crop_hz"],
                                            enabled=False)

    # ── 배치 텐서 입력 (시뮬 데이터셋 채점용) ────────────────
    @torch.no_grad()
    def forward_batch(self, X, V, sm):
        """이미 전처리·패딩된 배치 → (H정규화 예측(보정 적용), r정규화 예측)."""
        X, V, sm = X.to(self.device), V.to(self.device), sm.to(self.device)
        ph, _ = self.h_model(X, V, sm)   # H 전문가: 높이만 채택
        _, pr = self.r_model(X, V, sm)   # r 전문가: 반지름만 채택
        ph = ph.cpu().numpy()
        if self.calib is not None:
            a, b = self.calib
            ph = a * ph + b
        return ph, pr.cpu().numpy()

    # ── 단일 샘플 입력 (실측 데이터용) ───────────────────────
    @torch.no_grad()
    def predict(self, spec_seq, v_seq):
        """물 붓기 시퀀스 1개 → 물리 단위 예측.

        입력:
          spec_seq : (S, 700) — 스텝별 log10|H(f)| 스펙트럼 (생성 그리드 700bins)
          v_seq    : (S,)     — 스텝별 누적 부은 부피 [m³]
        출력:
          H_mm  : float — 예측 높이 [mm] (보정 적용)
          r_mm  : (25,) — 슬롯별 예측 반지름 [mm]
        """
        if self.calib is None:
            raise RuntimeError("H 보정계수가 없습니다. 먼저 "
                               "`python v2\\evaluate.py --ckpt <H전문가.pt> --save` 실행.")
        spec, v = loader.augment_sequence(np.asarray(spec_seq, np.float32),
                                          np.asarray(v_seq, np.float64),
                                          self.pre_cfg, np.random.default_rng(0),
                                          signatures=None)
        S = len(spec)
        X = torch.from_numpy(spec).unsqueeze(0)                    # (1,S,bins)
        V = torch.from_numpy(v).unsqueeze(0)                       # (1,S)
        sm = torch.ones(1, S)                                      # 패딩 없음
        ph, pr = self.forward_batch(X, V, sm)
        H_mm = (config.H_MIN + ph[0] * (config.H_MAX - config.H_MIN)) * 1000
        r_mm = (config.R_MIN + pr[0] * (config.R_MAX - config.R_MIN)) * 1000
        return float(H_mm), r_mm


# ─────────────────────────────────────────────────────────────
# 시뮬 테스트셋 채점 (전문가 결합 vs 단일 모델 비교용)
# ─────────────────────────────────────────────────────────────
def evaluate_combined(h_ckpt, r_ckpt, data_dir="dataset/v2", batch=64,
                      workers=0, device=None, max_samples=None):
    cp = CombinedPredictor(h_ckpt, r_ckpt, device)

    # 분할 재구성: r 전문가(메인 체크포인트)에 저장된 split을 우선 사용.
    split = cp.r_ckpt.get("split") or cp.h_ckpt.get("split") or {}
    split_seed = split.get("seed", 42)
    if max_samples is None:
        max_samples = split.get("max_samples")

    aug_cfg = loader.AugmentConfig(mode=cp.aug["mode"], crop_hz=cp.aug["crop_hz"])
    store, idx, _, ds_va, ds_te, collate = build_datasets(
        data_dir, aug_cfg, max_samples, split_seed=split_seed)
    dl_va = DataLoader(ds_va, batch_size=batch, shuffle=False,
                       collate_fn=collate, num_workers=workers)
    dl_te = DataLoader(ds_te, batch_size=batch, shuffle=False,
                       collate_fn=collate, num_workers=workers)

    print(f"\n{'=' * 62}\n결합 채점: H={os.path.basename(h_ckpt)}"
          f"\n          r={os.path.basename(r_ckpt)}\n{'=' * 62}")

    # H 보정계수가 없으면 검증셋에서 즉석 적합 (evaluate.py와 같은 방법).
    if cp.calib is None:
        vp_h, vt_h, *_ = run_inference(cp.h_model, dl_va, cp.device)
        cp.calib = fit_h_calibration(vp_h, vt_h)
        print(f"[CALIB] H 보정계수 즉석 적합: true ≈ {cp.calib[0]:.3f}·pred + {cp.calib[1]:.3f}"
              f"   (evaluate.py --save 로 저장해 두면 이 단계 생략)")

    # 테스트셋 채점 — H는 H 전문가(보정 포함), r은 r 전문가.
    ph_all, pr_all, yh_all, yr_all, lm_all = [], [], [], [], []
    for X, V, sm, yh, yr, lm, _stop in dl_te:
        ph, pr = cp.forward_batch(X, V, sm)
        ph_all.append(ph); pr_all.append(pr)
        yh_all.append(yh.numpy()); yr_all.append(yr.numpy()); lm_all.append(lm.numpy())
    ph = np.concatenate(ph_all); pr = np.concatenate(pr_all)
    yh = np.concatenate(yh_all); yr = np.concatenate(yr_all); lm = np.concatenate(lm_all)

    # 주의: forward_batch가 이미 보정을 적용했으므로 여기서는 calib=None으로 채점.
    h_cal = h_mae_mm(ph, yh)
    r_all = r_mae_mm_overall(pr, yr, lm)
    print(f"[TEST] 결합 성적: H_MAE(보정 후) {h_cal:6.2f}mm | r_MAE {r_all:5.2f}mm"
          f"  (샘플 {len(ph)}개)")

    print("\n[TEST] 슬롯별 r_MAE:")
    print("  슬롯   구간(mm)    샘플수   MAE(mm)")
    for s, lo, hi, cnt, mae in r_mae_mm_per_slot(pr, yr, lm):
        bar = "#" * min(int(round(mae * 4)), 60)
        print(f"  {s:3d}  {lo:4.0f}~{hi:4.0f}   {cnt:6d}   {mae:6.2f}  {bar}")

    print("\n(비교 기준) 지금까지 단일 모델 최고 기록:"
          "\n  H: CNN base_ratio_v2 보정 후 4.38mm | r: rnn_continuity ~1.5-1.8mm"
          "\n  결합이 두 기록을 동시에 달성하면 성공.")
    return {"H_MAE_calibrated_mm": h_cal, "r_MAE_mm": r_all}


def main():
    ap = argparse.ArgumentParser(description="H 전문가 + r 전문가 결합 채점")
    ap.add_argument("--h_ckpt", required=True, help="H(높이) 전문가 .pt")
    ap.add_argument("--r_ckpt", required=True, help="r(반지름) 전문가 .pt (예: rnn_continuity)")
    ap.add_argument("--data", default="dataset/v2")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--device", default=None)
    ap.add_argument("--samples", type=int, default=None, help="(디버그용) 일부 샘플만")
    a = ap.parse_args()
    evaluate_combined(a.h_ckpt, a.r_ckpt, a.data, a.batch, a.workers,
                      a.device, max_samples=a.samples)


if __name__ == "__main__":
    main()
