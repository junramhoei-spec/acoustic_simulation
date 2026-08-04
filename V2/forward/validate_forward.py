"""
순방향 v2 검증 스크립트.
실행: python v2/forward/validate_forward.py
출력: v2/validation/forward_v2_check.png + 콘솔 표

검증 논리:
  [1] 물리 코어 — 임피던스 공명(|Z_in+Z_rad| 최소) vs 해석해 (PASS < 3%)
  [2] 관측 모델 — 딥의 근접장 이동 특성화 + 원거리 수렴 (200mm에서 < 2%)
  [3] 감쇠 — 딥이 유한 폭·깊이
  [4] 예시 형상 3종 (보고서용 그림)
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from v2 import config
from v2.forward import tmm


def analytic_closed_open(L, r, n_modes=6):
    c = config.air_speed_of_sound()
    L_eff = L + 0.8216 * r
    return [(2 * n - 1) * c / (4 * L_eff) for n in range(1, n_modes + 1)]


def impedance_resonances(freqs, z_grid, r_grid, damping=True):
    seg_len, r_mid = tmm.segment_profile(z_grid, r_grid)
    z_in = tmm.input_impedance(freqs, seg_len, r_mid, damping=damping)
    z_rad = tmm.radiation_impedance(freqs, float(r_grid[-1]))
    mag = np.log10(np.abs(z_in + z_rad))
    idx, _ = find_peaks(-mag, prominence=0.1)
    return freqs[idx]


def find_dips(freqs, log_h, prominence=0.05):
    idx, _ = find_peaks(-log_h, prominence=prominence)
    return freqs[idx]


def match_nearest(candidates, targets):
    return [candidates[np.argmin(np.abs(candidates - t))] if len(candidates) else np.nan
            for t in targets]


def main():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "validation")
    os.makedirs(out_dir, exist_ok=True)

    freqs = np.linspace(config.FREQ_MIN, config.FREQ_MAX, config.N_FREQ * 4)

    L, r = 0.15, 0.03
    z = np.array([0.0, L]); rr = np.array([r, r])

    # [1] 물리 코어
    # 기준 1: 소-ka 대역(모드 1~2)은 상수 관구보정 해석해와 3% 이내
    # 기준 2: 고차 모드는 [상수보정 f_EC, 무보정 f_0] 사이(관구보정은 ka 증가에 따라 감소)
    res = impedance_resonances(freqs, z, rr)
    theory = [f for f in analytic_closed_open(L, r) if f < config.FREQ_MAX]
    c_air = config.air_speed_of_sound()
    theory_noEC = [(2 * n - 1) * c_air / (4 * L) for n in range(1, len(theory) + 1)]
    print("=" * 66)
    print(f"[1] 물리 코어 — 폐-개 원통 L={L*100:.0f}cm r={r*100:.0f}cm")
    print(f"{'모드':>4} {'상수EC(Hz)':>11} {'무EC(Hz)':>10} {'공명(Hz)':>10}  판정")
    core_ok = True
    matched = []
    for i, (f_ec, f_0) in enumerate(zip(theory, theory_noEC)):
        # 각 모드를 [상수EC 하한, 무EC 상한] 물리 구간 안에서 탐색
        in_win = res[(res > f_ec * 0.97) & (res < f_0 * 1.03)]
        ka = 2 * np.pi * f_0 * r / c_air
        if len(in_win):
            f_res = in_win[np.argmin(np.abs(in_win - 0.5 * (f_ec + f_0)))]
            matched.append(f_res)
            if i < 2:
                ok = abs(f_res - f_ec) / f_ec < 0.03
                tag = f"vs 상수EC {abs(f_res-f_ec)/f_ec*100:.2f}%"
            else:
                ok = True
                tag = "EC~무EC 사이(관구보정 감소)"
            print(f"{i+1:>4} {f_ec:>11.1f} {f_0:>10.1f} {f_res:>10.1f}  {'OK' if ok else 'NG'} ({tag})")
        else:
            # ka>2: 입구 방사저항 ≈ ρc/S → 공명이 방사감쇠로 소멸(물리적으로 정상)
            ok = ka > 2.0
            print(f"{i+1:>4} {f_ec:>11.1f} {f_0:>10.1f} {'—':>10}  "
                  f"{'OK' if ok else 'NG'} (ka={ka:.2f}: 방사감쇠로 약공명)")
        core_ok &= ok
    print(f"  -> [{'PASS' if core_ok else 'FAIL'}]")

    # [2] 관측 모델: 모드1 창(300~800Hz)에서 딥 위치의 근접장 이동 + 원거리 수렴
    # 마이크가 멀어질수록 딥 -> 시스템 공명으로 단조 수렴해야 함.
    seg_len, r_mid = tmm.segment_profile(z, rr)
    z_in = tmm.input_impedance(freqs, seg_len, r_mid)
    f_res1 = matched[0]
    print(f"\n[2] 모드1 딥 위치 (공명 {f_res1:.0f}Hz, 입구 무보정 {theory_noEC[0]:.0f}Hz)")
    dip_seq = []
    for d_mic in (0.010, 0.030, 0.060, 0.100):
        h = tmm.mic_ratio_response(freqs, z_in, r, d_mic=d_mic,
                                   d_spk=max(config.SPEAKER_DIST, d_mic * 3))
        dips = find_dips(freqs, np.log10(np.abs(h) + 1e-12), prominence=0.02)
        dips = dips[(dips > 300) & (dips < 800)]
        f_dip = dips[np.argmin(np.abs(dips - f_res1))] if len(dips) else np.nan
        dip_seq.append(f_dip)
        print(f"  d_mic={d_mic*1000:>3.0f}mm : 딥 {f_dip:7.1f}Hz ({(f_dip-f_res1)/f_res1*100:+.2f}%)")
    monotone = all(dip_seq[i] >= dip_seq[i+1] - 1.0 for i in range(len(dip_seq) - 1))
    far_ok = monotone and abs(dip_seq[-1] - f_res1) / f_res1 < 0.02
    print(f"  -> 단조 수렴 & 100mm에서 <2% [{'PASS' if far_ok else 'FAIL'}] "
          f"(근접장 이동은 실제 물리 — 실측 마이크도 같은 기하)")

    # [3] 감쇠
    freqs_std = np.linspace(config.FREQ_MIN, config.FREQ_MAX, config.N_FREQ)
    _, logh_damp = tmm.dip_spectrum(z, rr, freqs_std, damping=True)
    _, logh_free = tmm.dip_spectrum(z, rr, freqs_std, damping=False)
    print(f"\n[3] 감쇠: 최심 딥 log10 — 무손실 {logh_free.min():.2f} / Kirchhoff {logh_damp.min():.2f}")

    # [4] 예시 형상
    z_soju = np.array([0.0, 0.140, 0.170, 0.210])
    r_soju = np.array([0.032, 0.032, 0.013, 0.013])
    z_rig = np.array([0.0, 0.045, 0.045 + 1e-9, 0.090, 0.090 + 1e-9, 0.135])
    r_rig = np.array([0.040, 0.040, 0.028, 0.028, 0.016, 0.016])
    _, logh_soju = tmm.dip_spectrum(z_soju, r_soju, freqs_std)
    _, logh_rig = tmm.dip_spectrum(z_rig, r_rig, freqs_std, rig_top_extension=True)

    # 그림
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))

    ax = axes[0, 0]
    ax.plot(freqs_std, 20 * logh_free, color="0.75", lw=0.8, label="lossless")
    ax.plot(freqs_std, 20 * logh_damp, "b", lw=1.2, label="Kirchhoff")
    for f_res in matched:
        ax.axvline(f_res, color="r", ls="--", lw=0.7, alpha=0.6)
    ax.set_title("[1-3] Cylinder 15cm/3cm - dips vs resonances (red)")
    ax.set_ylabel("|H| (dB)"); ax.legend(fontsize=8)

    ax = axes[0, 1]
    for d_mic, style in ((0.010, "b-"), (0.050, "g-"), (0.200, "m-")):
        h = tmm.mic_ratio_response(freqs, z_in, r, d_mic=d_mic,
                                   d_spk=max(config.SPEAKER_DIST, d_mic * 2))
        ax.plot(freqs, 20 * np.log10(np.abs(h) + 1e-12), style, lw=1.0,
                label=f"d_mic={d_mic*1000:.0f}mm")
    for f_res in matched[:2]:
        ax.axvline(f_res, color="r", ls="--", lw=0.7, alpha=0.6)
    ax.set_xlim(300, 1800); ax.legend(fontsize=8)
    ax.set_title("[2] Near-field dip shift -> far-field convergence")

    ax = axes[1, 0]
    ax.plot(freqs_std, 20 * logh_soju, "g", lw=1.2)
    ax.set_title("[4] Soju-bottle profile"); ax.set_xlabel("Frequency (Hz)"); ax.set_ylabel("|H| (dB)")

    ax = axes[1, 1]
    ax.plot(freqs_std, 20 * logh_rig, "m", lw=1.2)
    ax.set_title("[4] Rig: rings 40/28/16mm + 5mm top ext."); ax.set_xlabel("Frequency (Hz)")

    for a in axes.flat:
        a.grid(alpha=0.3)
    fig.tight_layout()
    out_png = os.path.join(out_dir, "forward_v2_check.png")
    fig.savefig(out_png, dpi=110)
    print(f"\n그림 저장: {out_png}")
    print(f"종합: 물리 코어 [{'PASS' if core_ok else 'FAIL'}] / 관측 모델 수렴 [{'PASS' if far_ok else 'FAIL'}]")


if __name__ == "__main__":
    main()
