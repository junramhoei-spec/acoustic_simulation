# -*- coding: utf-8 -*-
"""TTR v0 배치 실행 — 리그 10컵(참값 내장 JSON) 채점.

실행 (프로젝트 루트 acoustic_simulation\ 에서):
    python v2\ttr\run_ttr_rig10.py

전제:
  - 체크포인트: dataset\models_v2\rnn_sline_nodetach_bestH.pt / rnn_sline_uni.pt
  - 실측 JSON:  v2\real_measured_json_all\*.json (true_H_mm/true_r_mm 포함)
출력: v2\ttr\ttr_rig10_results.csv
"""
import os, sys, json, time, csv
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from v2.combine import CombinedPredictor
from v2.ttr.ttr_v0 import ttr_refine

CKPT_H = os.path.join("dataset", "models_v2", "rnn_sline_nodetach_bestH.pt")
CKPT_R = os.path.join("dataset", "models_v2", "rnn_sline_uni.pt")
JSON_DIR = os.path.join("v2", "real_measured_json_all")

CUPS = [
 ("01_일자형컵_105mm_r40mm.json", "#14 일자105"),
 ("02_벌어진컵_120mm_갈갈초초흰흰검검.json", "#15 벌120"),
 ("03_벌어진컵_90mm_초초검검파파.json", "#16 벌90"),
 ("04_오므라드는컵_90mm_파파검검초초.json", "#17 오므90"),
 ("05_오므라드는컵_120mm_파파파검검검초초.json", "#18 오므120"),
 ("06_중앙볼록컵_105mm_초흰검파검흰초.json", "#19 볼록105"),
 ("07_중앙볼록컵_120mm_갈초흰검검흰초갈.json", "#20 볼록120"),
 ("18_일자컵_150mm_r40mm.json", "#11 일자150r40"),
 ("19_일자컵_150mm_r50mm.json", "#12 일자150r50"),
 ("20_벌어진컵1_90mm_초초검검파파.json", "#13 벌90오전"),
]

def main():
    cp = CombinedPredictor(CKPT_H, CKPT_R, device="cpu")
    rows = []
    for fn, label in CUPS:
        path = os.path.join(JSON_DIR, fn)
        if not os.path.exists(path):
            print(f"[스킵] {fn} 없음"); continue
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        spec = np.array(d["spectra_log10"], np.float32)
        v = np.array(d["v_cum_m3"])
        tH = d["true_H_mm"]; tr = np.array(d["true_r_mm"]); n = int(sum(d["true_mask"]))
        H0, r0 = cp.predict(spec, v)
        t0 = time.time()
        H1, r1, delta, _ = ttr_refine(spec, v, H0, r0, iters=120, verbose=False)
        e0, e1 = H0-tH, H1-tH
        m0 = float(np.mean(np.abs(r0[:n]-tr[:n]))); m1 = float(np.mean(np.abs(r1[:n]-tr[:n])))
        rows.append([label, tH, round(H0,1), round(H1,1), round(e0,1), round(e1,1),
                     round(m0,2), round(m1,2), round(delta,1)])
        print(f"{label:16s} 참H={tH:5.1f} NN={H0:6.1f}({e0:+.1f}) TTR={H1:6.1f}({e1:+.1f}) "
              f"| r_MAE {m0:5.2f}→{m1:5.2f} | δ={delta:4.1f}mm [{time.time()-t0:.0f}s]", flush=True)

    if rows:
        eH0 = np.mean([abs(r[4]) for r in rows]); eH1 = np.mean([abs(r[5]) for r in rows])
        m0s = np.mean([r[6] for r in rows]); m1s = np.mean([r[7] for r in rows])
        print(f"\n== 평균: |H오차| NN {eH0:.1f} → TTR {eH1:.1f} mm | r_MAE NN {m0s:.2f} → TTR {m1s:.2f} mm ==")
        out = os.path.join("v2", "ttr", "ttr_rig10_results.csv")
        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["컵","참H","NN_H","TTR_H","NN오차","TTR오차","NN_rMAE","TTR_rMAE","delta_mm"])
            w.writerows(rows)
        print(f"[저장] {out}")

if __name__ == "__main__":
    main()
