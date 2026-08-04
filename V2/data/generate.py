"""
데이터 생성기 v1 — §4 프로토콜 (2026-07-02 확정)
  고정 ΔV=10mL / 정지: 잔여 공기기둥 30mm / 최소부피 40mL / 최대 128스텝 캡
  스텝 0 = 빈 컵. 온도 20°C 고정 생성(온도는 증강에서 주파수축 리샘플로 처리).

실행: python v2/data/generate.py --samples 1000 --out dataset/v2 --worker_id 1
저장(래그드 CSR — 컵마다 스텝 수가 달라 패딩 없이 이어붙임):
  spectra_all : (총스텝, 700) float16 — log10|H| 딥 스펙트럼
  v_cum_all   : (총스텝,)    float32 — 해당 스텝까지 부은 누적 부피 [m³]
  h_all       : (총스텝,)    float16 — 수위 [m] (디버그용. 입력 사용 금지: 정답 파생)
  n_steps     : (N,) int16   — 샘플별 스텝 수 (offsets = cumsum)
  H           : (N,) float32 — 공동 높이 [m]
  labels      : (N, 25) float32 — 슬롯 등가반지름 [m]
  label_mask  : (N, 25) float32 — 유효 슬롯
"""
import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from v2 import config
from v2.data import shapes
from v2.forward import tmm

DELTA_V = 10e-6
AIR_STOP = 0.030
V_MIN_FILL = 4 * DELTA_V
MAX_STEPS = 128


def simulate_sample(rng, freqs):
    z, r = shapes.sample_profile(rng)
    H = float(z[-1])
    zz, V = shapes.volume_profile(z, r)
    v_stop = float(np.interp(max(H - AIR_STOP, 0.0), zz, V))
    if v_stop < V_MIN_FILL:
        return None

    n_pours = min(int(v_stop / DELTA_V), MAX_STEPS)
    v_cum = np.arange(n_pours + 1) * DELTA_V
    heights = np.interp(v_cum, V, zz)

    spectra = np.empty((n_pours + 1, len(freqs)), dtype=np.float16)
    for i, wh in enumerate(heights):
        m = zz >= wh
        za = zz[m] - wh
        ra = np.interp(zz[m], z, r)
        _, lh = tmm.dip_spectrum(za, ra, freqs)
        spectra[i] = lh.astype(np.float16)

    labels, mask = shapes.slot_labels(z, r)
    return spectra, v_cum.astype(np.float32), heights.astype(np.float16), H, labels, mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=1000)
    ap.add_argument("--chunk", type=int, default=2000)
    ap.add_argument("--out", default="dataset/v2")
    ap.add_argument("--worker_id", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    seed = args.seed if args.seed is not None else 1000 + args.worker_id
    rng = np.random.default_rng(seed)
    freqs = np.linspace(config.FREQ_MIN, config.FREQ_MAX, config.N_FREQ)

    done, chunk_idx, t0 = 0, 1, time.time()
    buf = {k: [] for k in ("spectra", "v", "h", "H", "labels", "mask", "n")}

    while done < args.samples:
        out = simulate_sample(rng, freqs)
        if out is None:
            continue
        sp, v, h, H, lab, msk = out
        buf["spectra"].append(sp); buf["v"].append(v); buf["h"].append(h)
        buf["H"].append(H); buf["labels"].append(lab); buf["mask"].append(msk)
        buf["n"].append(len(v))
        done += 1

        if done % 100 == 0:
            rate = done / (time.time() - t0)
            eta = (args.samples - done) / rate / 60
            print(f"[w{args.worker_id}] {done}/{args.samples}  {rate:.1f}/s  ETA {eta:.1f}min", flush=True)

        if len(buf["n"]) >= args.chunk or done >= args.samples:
            path = os.path.join(args.out, f"v2_chunk_w{args.worker_id}_{chunk_idx:03d}.npz")
            np.savez_compressed(
                path,
                spectra_all=np.concatenate(buf["spectra"], axis=0),
                v_cum_all=np.concatenate(buf["v"]),
                h_all=np.concatenate(buf["h"]),
                n_steps=np.array(buf["n"], dtype=np.int16),
                H=np.array(buf["H"], dtype=np.float32),
                labels=np.stack(buf["labels"]),
                label_mask=np.stack(buf["mask"]),
                meta=np.array([DELTA_V, AIR_STOP, config.FREQ_MIN, config.FREQ_MAX,
                               config.N_FREQ, config.AIR_TEMP_C]),
            )
            print(f"[SAVED] {path} ({len(buf['n'])} samples)", flush=True)
            buf = {k: [] for k in buf}
            chunk_idx += 1

    print(f"[DONE] worker {args.worker_id}: {done} samples in {(time.time()-t0)/60:.1f}min")


if __name__ == "__main__":
    main()
