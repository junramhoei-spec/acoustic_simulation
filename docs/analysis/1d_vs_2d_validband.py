"""
1D 평면파 TMM vs 2D 축대칭(on-axis) 공명 주파수 비교 — 유효대역 검증
=====================================================================
목적: 측정 대역(50~5000Hz)에서 1D TMM이 2D 축대칭 대비 유효한지 수치로 확인.

방법:
  폐-개 원형 실린더 공동(공기기둥)의 고유모드를 해석적으로 계산.
  - 축 방향(closed-open): k_z = (2q-1)·π / (2·L_eff),  q=1,2,...
  - 반지름 방향(rigid wall, m=0): k_r = α_p / a,  α_p = J0' 의 p번째 근
      (p=0 → k_r=0 = 평면파(=1D) 계열,  p≥1 → 2D가 추가하는 반경 모드)
  - f = c·sqrt(k_z² + k_r²) / (2π)
  on-axis 마이크는 각 모드(m≥1)를 못 봄(축상 마디)이라 m=0만 고려.
  실린더는 "반경 차단이 가장 낮은" 최악 케이스(넓을수록 낮음)라 상한 검증에 적합.

결론(아래 출력): r≤4cm에서 첫 반경 모드가 ≥5259Hz(대역 밖) → 대역 내 1D=2D.
"""
import numpy as np
from scipy.special import jnp_zeros
import matplotlib.pyplot as plt

C = 331.3 + 0.606 * 20.0          # 343.42 m/s  (core/materials.py 와 동일)
FMAX = 5000.0                     # 측정 대역 상한
ALPHA = np.concatenate([[0.0], jnp_zeros(0, 4)])   # J0' 근 (반경 m=0 고유값)


def modes_1d(a, L, fmax):
    """1D 축 방향(평면파) 공명."""
    Le = L + 0.6133 * a           # unflanged 관구보정
    fs, q = [], 1
    while True:
        f = (2 * q - 1) * C / (4 * Le)
        if f > fmax * 1.4:
            break
        fs.append(f); q += 1
    return np.array(fs)


def modes_2d_onaxis(a, L, fmax):
    """2D 축대칭 on-axis(m=0) 공명: (f, p=반경차수, q=축차수)."""
    Le = L + 0.6133 * a
    out = []
    for p, al in enumerate(ALPHA):
        kr, q = al / a, 1
        while True:
            kz = (2 * q - 1) * np.pi / (2 * Le)
            f = C * np.hypot(kz, kr) / (2 * np.pi)
            if f > fmax * 1.4:
                break
            out.append((f, p, q)); q += 1
    out.sort()
    return out


def summary_table():
    print("c = %.1f m/s,  band = 50..%.0f Hz\n" % (C, FMAX))
    hdr = ("r(cm)", "L(cm)", "0.61c/a", "1st radial f(1,1)", "#1D in band", "#extra 2D in band")
    print("%5s %5s %10s %18s %12s %18s" % hdr)
    for a_cm in (1.0, 2.0, 4.0):
        for L_cm in (5.0, 15.0):
            a, L = a_cm / 100, L_cm / 100
            f1d = modes_1d(a, L, FMAX)
            m2d = modes_2d_onaxis(a, L, FMAX)
            rad = [f for f, p, q in m2d if p >= 1]
            first_rad = min(rad) if rad else float("inf")
            n1d = int(((f1d >= 50) & (f1d <= FMAX)).sum())
            n_extra = sum(1 for f, p, q in m2d if p >= 1 and 50 <= f <= FMAX)
            print("%5.0f %5.0f %10.0f %18.0f %12d %18d"
                  % (a_cm, L_cm, 0.61 * C / a, first_rad, n1d, n_extra))


def make_figure(path):
    """최악 케이스(r=4cm, L=15cm) 공명 배치 그림."""
    a, L = 0.04, 0.15
    f1d = modes_1d(a, L, 6000)
    m2d = modes_2d_onaxis(a, L, 6000)
    fig, ax = plt.subplots(figsize=(9, 2.6))
    ax.axvspan(50, FMAX, color="tab:green", alpha=0.08, label="Measurement band 50-5000 Hz")
    for f in f1d:
        if f <= 6000:
            ax.axvline(f, color="tab:blue", lw=2)
    for f, p, q in m2d:
        if p >= 1 and f <= 6000:
            ax.axvline(f, color="tab:red", lw=2, ls="--")
    ax.axvline(0.61 * C / a, color="k", lw=1, ls=":", label="Radial cutoff 0.61c/a")
    ax.plot([], [], color="tab:blue", lw=2, label="1D axial modes (= 2D p=0)")
    ax.plot([], [], color="tab:red", lw=2, ls="--", label="2D extra radial modes (p>=1)")
    ax.set_xlim(0, 6000); ax.set_yticks([])
    ax.set_xlabel("Frequency (Hz)")
    ax.set_title("1D vs 2D axisymmetric resonances — cylinder r=4cm, L=15cm (worst case)")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)
    print("\n[figure saved] %s" % path)


if __name__ == "__main__":
    summary_table()
    print("\n--- detail: r=4cm, L=15cm ---")
    for f, p, q in modes_2d_onaxis(0.04, 0.15, 6000):
        if 50 <= f <= 6000:
            tag = "  <-- RADIAL (new in 2D)" if p >= 1 else ""
            print("   %7.0f Hz  (p=%d, q=%d)%s" % (f, p, q, tag))
    import os
    make_figure(os.path.join(os.path.dirname(os.path.abspath(__file__)), "1d_vs_2d_validband.png"))
