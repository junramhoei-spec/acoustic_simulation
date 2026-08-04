"""
ΔV 스터디 (§12 TODO) — 고정 ΔV·정지기준·최소부피 제약을 데이터로 결정.
실행: python v2/data/dv_study.py
출력: v2/validation/dv_study.png + 콘솔 표

프로토콜 가정:
  - 정지 기준: 잔여 공기기둥 높이 <= AIR_STOP(30mm)가 '되기 직전'까지 ΔV씩 붓기
  - 측정 상태 수 = 빈 컵(스텝0) + 부은 횟수
  - 스텝당 시간 = 스윕2s + 안정화2s = 4s 가정
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from v2 import config
from v2.data import shapes

AIR_STOP = 0.030      # m — 잔여 공기기둥 정지 기준
SEC_PER_STEP = 4.0
N_SAMPLES = 20000
DV_CANDIDATES = [10e-6, 20e-6, 30e-6, 50e-6]   # m³ (10~50 mL)
MIN_STEPS_TARGET = 5   # 이보다 적으면 유체 채널 정보 부족으로 판단


def main():
    rng = np.random.default_rng(42)
    vols_fill = []     # 정지 기준까지 부어야 하는 부피
    rise_stats = []    # (컵별) 스텝당 수위 상승 중앙값 계산용 면적
    heights = []
    for _ in range(N_SAMPLES):
        z, r = shapes.sample_profile(rng)
        H = z[-1]
        zz, V = shapes.volume_profile(z, r)
        v_target = np.interp(max(H - AIR_STOP, 0.0), zz, V)
        vols_fill.append(v_target)
        heights.append(H)
        # 대표 단면적(중앙값) → 스텝당 상승 근사용
        rr = np.interp(np.linspace(0, max(H - AIR_STOP, 1e-3), 50), z, r)
        rise_stats.append(np.median(np.pi * rr ** 2))
    vols_fill = np.array(vols_fill); A_med = np.array(rise_stats); heights = np.array(heights)

    print("=" * 78)
    print(f"형상 {N_SAMPLES}개 샘플링 (r∈[5,50]mm, H∈[30,250]mm, 정지기준: 공기기둥 {AIR_STOP*1000:.0f}mm)")
    print(f"부어야 할 부피: 중앙값 {np.median(vols_fill)*1e6:.0f}mL / "
          f"5% {np.percentile(vols_fill,5)*1e6:.0f}mL / 95% {np.percentile(vols_fill,95)*1e6:.0f}mL / "
          f"최대 {vols_fill.max()*1e6:.0f}mL")
    print()
    hdr = (f"{'ΔV(mL)':>7} {'스텝<5 비율':>10} {'스텝 중앙값':>10} {'스텝 95%':>9} {'최대':>5} "
           f"{'최대시간(분)':>11} {'상승중앙(mm)':>11} {'상승95%(mm)':>11}")
    print(hdr)
    rows = []
    for dv in DV_CANDIDATES:
        steps = np.floor(vols_fill / dv).astype(int) + 1   # 빈 컵 포함
        rise = dv / A_med * 1000                            # mm/스텝 (중앙값 면적 기준)
        frac_short = np.mean(steps < MIN_STEPS_TARGET) * 100
        rows.append((dv, steps, rise))
        print(f"{dv*1e6:>7.0f} {frac_short:>9.1f}% {np.median(steps):>10.0f} "
              f"{np.percentile(steps,95):>9.0f} {steps.max():>5d} "
              f"{steps.max()*SEC_PER_STEP/60:>11.1f} {np.median(rise):>11.1f} "
              f"{np.percentile(rise,95):>11.1f}")

    # 최소부피 제약 후보: 각 ΔV에서 스텝>=5를 보장하는 부피 하한 = (5-1)*ΔV
    print()
    for dv in DV_CANDIDATES:
        vmin = (MIN_STEPS_TARGET - 1) * dv
        excl = np.mean(vols_fill < vmin) * 100
        print(f"  ΔV={dv*1e6:.0f}mL → 최소부피 제약 {vmin*1e6:.0f}mL 필요, 분포의 {excl:.1f}% 배제")

    # 그림
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    axes[0].hist(vols_fill * 1e6, bins=60, color="#3b82f6")
    axes[0].set_xlabel("Fill volume to stop (mL)"); axes[0].set_title("Volume distribution")
    for dv, steps, rise in rows:
        axes[1].hist(steps, bins=60, histtype="step", lw=1.4, label=f"dV={dv*1e6:.0f}mL")
        axes[2].hist(np.clip(rise, 0, 80), bins=60, histtype="step", lw=1.4, label=f"dV={dv*1e6:.0f}mL")
    axes[1].set_xlabel("Number of steps"); axes[1].set_title("Steps per cup"); axes[1].legend(fontsize=8)
    axes[1].axvline(MIN_STEPS_TARGET, color="r", ls="--", lw=0.8)
    axes[2].set_xlabel("Median water rise per step (mm)"); axes[2].set_title("Rise vs 10mm slot pitch")
    axes[2].axvline(10, color="r", ls="--", lw=0.8)
    axes[2].legend(fontsize=8)
    for a in axes: a.grid(alpha=0.3)
    fig.tight_layout()
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "validation", "dv_study.png")
    fig.savefig(out, dpi=110)
    print(f"\n그림 저장: {out}")


if __name__ == "__main__":
    main()
