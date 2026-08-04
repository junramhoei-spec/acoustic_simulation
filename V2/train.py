"""
학습 스크립트 v1 — 베이스라인 CNN (§8 1칸).
CLI:  python v2/train.py --data dataset/v2 --mode ratio --epochs 30 --name base_ratio
      python v2/train.py --model rnn --mode ratio --epochs 30 --name rnn_ratio   (§8 2칸)
앱(3번 탭)에서는 train()을 직접 호출(progress_cb로 진행 표시).

체크포인트(dataset/models_v2/{name}.pt):
  model_state / arch{n_bins,d} / aug{mode,crop} / split{seed,test_idx}
  / history / 물리상수 스냅샷(정규화 기준 재현용)
"""
import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2 import config
from torch.utils.data import Dataset
import torch

from v2.data import loader
from v2.models import continuity
from v2.models.baseline import MaskedSetBaseline, masked_loss, mae_mm


class ChunkDataset(Dataset):
    def __init__(self, store, aug_cfg, signatures, indices, deterministic):
        self.store = store
        self.aug_cfg = aug_cfg
        self.signatures = signatures
        self.indices = indices
        self.det = deterministic

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, k):
        i = int(self.indices[k])
        rng = np.random.default_rng((1234, i)) if self.det else np.random.default_rng()
        spec, v, H, lab, lm = self.store.get_raw(i)
        spec, v = loader.augment_sequence(spec, v, self.aug_cfg, rng, self.signatures)
        h_n, r_n = loader.normalize_labels(H, lab)
        # 연속방정식 잔차용: 원본(서브샘플 전) 스텝 수로 MAX_STEPS 캡 여부 판정
        stop_valid = continuity.is_stop_valid(int(self.store.n_steps[i]))
        return spec, v, h_n, r_n, lm, stop_valid


class ChunkCollate:
    def __init__(self, n_bins):
        self.n_bins = n_bins

    def __call__(self, batch):
        core = [b[:5] for b in batch]
        arrs = loader.collate_numpy(core, self.n_bins)
        stop_valid = np.array([b[5] for b in batch], dtype=np.float32)
        return tuple(torch.from_numpy(a) for a in arrs) + (torch.from_numpy(stop_valid),)


def build_datasets(data_dir, aug_cfg, max_samples, split_seed=42):
    store = loader.ChunkStore(data_dir, max_samples=max_samples)
    n = len(store)
    perm = np.random.default_rng(split_seed).permutation(n)
    n_tr, n_va = int(n * 0.8), int(n * 0.1)
    idx = {"train": perm[:n_tr], "val": perm[n_tr:n_tr + n_va], "test": perm[n_tr + n_va:]}

    base_rng = np.random.default_rng(0)
    signatures = loader.load_or_synth_signatures(aug_cfg, base_rng)

    ds_tr = ChunkDataset(store, aug_cfg, signatures, idx["train"], False)
    ds_va = ChunkDataset(store, aug_cfg, signatures, idx["val"], True)
    ds_te = ChunkDataset(store, aug_cfg, signatures, idx["test"], True)
    collate = ChunkCollate(aug_cfg.n_bins)

    return store, idx, ds_tr, ds_va, ds_te, collate


def build_model(model_type, n_bins, dropout=0.2, **model_kw):
    """§8 사다리 팩토리. set=1칸(CNN 셋 풀링), rnn=2칸(BiLSTM).
    dropout은 양 사다리에 동일 적용 → A5 공정 비교(같은 정규화 레짐)."""
    if model_type == "rnn":
        from v2.models.rnn import MaskedSeqRNN
        return MaskedSeqRNN(n_bins, dropout=dropout, **model_kw)
    return MaskedSetBaseline(n_bins, dropout=dropout)


def train(data_dir="dataset/v2", mode="ratio", crop=config.CROP_DEFAULT,
          epochs=30, batch=64, lr=1e-3, max_samples=None, device=None,
          name="base_ratio", h_weight=3.0, num_workers=0, progress_cb=None,
          model_type="set", model_kw=None, weight_decay=1e-4, dropout=0.2,
          early_patience=0, c_weight=1.0):
    import torch
    from torch.utils.data import DataLoader

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    aug_cfg = loader.AugmentConfig(mode=mode, crop_hz=crop)
    store, idx, ds_tr, ds_va, ds_te, collate = build_datasets(data_dir, aug_cfg, max_samples)
    print(f"[data] {len(store)} samples | bins={aug_cfg.n_bins} | mode={mode} "
          f"| model={model_type} | device={device}")

    dl_tr = DataLoader(ds_tr, batch_size=batch, shuffle=True, collate_fn=collate, num_workers=num_workers)
    dl_va = DataLoader(ds_va, batch_size=batch, shuffle=False, collate_fn=collate, num_workers=num_workers)

    model_kw = model_kw or {}
    model = build_model(model_type, aug_cfg.n_bins, dropout=dropout, **model_kw).to(device)
    # AdamW + weight decay: 형상 과적합(train<<val 갭) 억제
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs, eta_min=lr * 0.01)
    history, best_val, best_h = [], float("inf"), float("inf")
    os.makedirs("dataset/models_v2", exist_ok=True)
    ckpt_path = f"dataset/models_v2/{name}.pt"
    ckpt_h_path = f"dataset/models_v2/{name}_bestH.pt"
    # 에폭별 성분 로그 CSV — 콘솔과 무관하게 무조건 파일로 남김 (시소 판정 근거 유실 방지)
    log_path = f"dataset/models_v2/{name}_trainlog.csv"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("epoch,train_loss,train_l_r,train_l_h,train_l_c,val_loss,val_l_r,val_l_h,val_l_c,"
                "val_H_MAE_mm,val_r_MAE_mm,lr,elapsed_s\n")

    def run_epoch(dl, train_mode, collect=False):
        model.train(train_mode)
        tot, lr_sum, lh_sum, lc_sum, n_seen, h_mms, r_mms = 0.0, 0.0, 0.0, 0.0, 0, [], []
        preds, targs = [], []
        with torch.set_grad_enabled(train_mode):
            for X, V, sm, yh, yr, lm, stop_valid in dl:
                X, V, sm = X.to(device), V.to(device), sm.to(device)
                yh, yr, lm = yh.to(device), yr.to(device), lm.to(device)
                stop_valid = stop_valid.to(device)
                ph, pr = model(X, V, sm)
                loss, l_r, l_h = masked_loss(ph, pr, yh, yr, lm, h_weight)
                v_last = (V * sm).max(dim=1).values * config.V_NORM
                l_c = continuity.continuity_loss(pr, ph, v_last, stop_valid)
                loss = loss + c_weight * l_c
                if train_mode:
                    opt.zero_grad(); loss.backward(); opt.step()
                bs = X.size(0)
                tot += loss.item() * bs; n_seen += bs
                lr_sum += l_r.item() * bs; lh_sum += l_h.item() * bs
                lc_sum += l_c.item() * bs
                hm, rm = mae_mm(ph, pr, yh, yr, lm)
                h_mms.append(hm * bs); r_mms.append(rm * bs)
                if collect:
                    preds.append(ph.detach().cpu()); targs.append(yh.cpu())
        out = (tot / n_seen, sum(h_mms) / n_seen, sum(r_mms) / n_seen,
               lr_sum / n_seen, lh_sum / n_seen, lc_sum / n_seen)
        if collect:
            return out, torch.cat(preds).numpy(), torch.cat(targs).numpy()
        return out

    t0 = time.time()
    no_improve = 0
    for ep in range(1, epochs + 1):
        tr_loss, _, _, tr_lr, tr_lh, tr_lc = run_epoch(dl_tr, True)
        sched.step()
        va_loss, va_h, va_r, va_lr, va_lh, va_lc = run_epoch(dl_va, False)
        history.append((ep, tr_loss, va_loss, va_h, va_r, va_lr, va_lh))
        cur_lr = opt.param_groups[0]["lr"]
        elapsed = time.time() - t0
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{ep},{tr_loss:.6f},{tr_lr:.6f},{tr_lh:.6f},{tr_lc:.6f},"
                    f"{va_loss:.6f},{va_lr:.6f},{va_lh:.6f},{va_lc:.6f},"
                    f"{va_h:.2f},{va_r:.3f},{cur_lr:.2e},{elapsed:.0f}\n")
        msg = (f"[{ep:3d}/{epochs}] train {tr_loss:.5f} | val {va_loss:.5f} "
               f"(r {va_lr:.5f} h {va_lh:.5f} c {va_lc:.5f}) | H_MAE {va_h:6.1f}mm "
               f"| r_MAE {va_r:5.2f}mm | {elapsed:5.0f}s")
        print(msg, flush=True)
        if progress_cb:
            progress_cb(ep, epochs, msg, history)
        # 높이 단독 베스트도 별도 보존 (멀티태스크 시소 대비)
        if va_lh < best_h:
            best_h = va_lh
            torch.save({"model_state": model.state_dict(),
                        "arch": {"n_bins": aug_cfg.n_bins, "n_slots": config.N_SLOTS,
                                 "model": model_type, "model_kw": model_kw},
                        "aug": {"mode": mode, "crop_hz": crop},
                        "epoch": ep, "val_h_loss": va_lh}, ckpt_h_path)
        if va_loss < best_val:
            best_val = va_loss
            no_improve = 0
            import torch as _t
            _t.save({
                "model_state": model.state_dict(),
                "arch": {"n_bins": aug_cfg.n_bins, "n_slots": config.N_SLOTS,
                         "model": model_type, "model_kw": model_kw},
                "aug": {"mode": mode, "crop_hz": crop},
                "split": {"seed": 42, "test_idx": idx["test"].tolist(),
                          "max_samples": max_samples, "data_dir": data_dir},
                "norms": {"H_MIN": config.H_MIN, "H_MAX": config.H_MAX,
                          "R_MIN": config.R_MIN, "R_MAX": config.R_MAX,
                          "V_NORM": config.V_NORM},
                "history": history,
            }, ckpt_path)
        else:
            no_improve += 1
            if early_patience > 0 and no_improve >= early_patience:
                print(f"[EARLY STOP] val loss {early_patience} epoch 연속 미개선 -> ep {ep} 조기 종료")
                break

    # 미확인 테스트셋 최종 평가 (베스트 가중치) + 검증셋 기반 H 보정 내장
    ck = torch.load(ckpt_path, map_location=device, weights_only=False)
    model.load_state_dict(ck["model_state"])

    # H 선형 보정: 검증셋에서 (pred → true) 1차 적합. 조기 정체된 출력 눈금을 폄.
    (_, _, _, _, _, _), vp, vt = run_epoch(dl_va, False, collect=True)
    a_cal, b_cal = np.polyfit(vp, vt, 1)
    ck["calib_h"] = {"a": float(a_cal), "b": float(b_cal)}
    print(f"[CALIB] h_norm ~ {a_cal:.3f} * pred + {b_cal:.3f} (검증셋 적합, 추론 시 자동 적용)")

    dl_te = DataLoader(ds_te, batch_size=batch, shuffle=False, collate_fn=collate)
    (te_loss, te_h, te_r, _, _, _), tp, tt = run_epoch(dl_te, False, collect=True)
    te_h_cal = float(np.abs(a_cal * tp + b_cal - tt).mean() * (config.H_MAX - config.H_MIN) * 1000)
    print(f"[TEST] loss {te_loss:.5f} | H_MAE {te_h:.1f}mm (보정 후 {te_h_cal:.1f}mm) | r_MAE {te_r:.2f}mm")
    ck["test_metrics"] = {"loss": te_loss, "H_MAE_mm": te_h,
                          "H_MAE_calibrated_mm": te_h_cal, "r_MAE_mm": te_r}
    # 체크포인트 history는 베스트 시점까지만 담겨 있었음 → 전체 이력으로 교체 (판정 근거 보존)
    ck["history"] = history
    torch.save(ck, ckpt_path)
    print(f"[SAVED] {ckpt_path}")
    return ckpt_path, history


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="dataset/v2")
    ap.add_argument("--mode", choices=["ratio", "absolute"], default="ratio")
    ap.add_argument("--crop", type=float, default=config.CROP_DEFAULT)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--device", default=None)
    ap.add_argument("--name", default="base_ratio")
    ap.add_argument("--h_weight", type=float, default=3.0)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--smoke", action="store_true", help="초소형 동작 확인")
    ap.add_argument("--model", choices=["set", "rnn"], default="set",
                    help="set=CNN 셋 풀링(1칸) / rnn=BiLSTM(2칸)")
    ap.add_argument("--direction", choices=["bi", "uni", "rev"], default="bi",
                    help="[rnn] 읽기 방향 (어블레이션 A2)")
    ap.add_argument("--summary", choices=["mix", "last"], default="mix",
                    help="[rnn] 시퀀스 요약 방식 (어블레이션 A3)")
    ap.add_argument("--no_detach", action="store_true",
                    help="[rnn] H 헤드 gradient 분리 해제 (어블레이션 A4)")
    ap.add_argument("--weight_decay", type=float, default=1e-4,
                    help="AdamW L2 정규화 (과적합 억제, set/rnn 공통)")
    ap.add_argument("--dropout", type=float, default=0.2,
                    help="trunk dropout 비율 (과적합 억제, set/rnn 공통)")
    ap.add_argument("--dim", type=int, default=256,
                    help="모델 은닉 차원 d (기본 256, 과적합 시 128 권장)")
    ap.add_argument("--patience", type=int, default=0,
                    help="Early stopping patience (0=비활성, 권장 7~10)")
    ap.add_argument("--c_weight", type=float, default=1.0,
                    help="연속방정식 잔차 손실(∫A dh=Q·t 근사) 가중치, 0=비활성. "
                         "predicted r(z)+H가 실제 부은 부피(V_last)와 맞는지 강제.")
    a = ap.parse_args()
    if a.smoke:
        a.samples, a.epochs, a.batch = 48, 2, 8
        a.name += "_smoke"   # 본 체크포인트 덮어쓰기 방지
    mkw = ({"direction": a.direction, "summary": a.summary,
            "detach_h": not a.no_detach, "d": a.dim} if a.model == "rnn"
           else ({"d": a.dim} if a.dim != 256 else None))
    train(a.data, a.mode, a.crop, a.epochs, a.batch, a.lr, a.samples,
          a.device, a.name, a.h_weight, a.workers,
          model_type=a.model, model_kw=mkw,
          weight_decay=a.weight_decay, dropout=a.dropout,
          early_patience=a.patience, c_weight=a.c_weight)


if __name__ == "__main__":
    main()
