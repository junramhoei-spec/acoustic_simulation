"""
형상 생성기 v2 — §4 프로토콜.
연속 랜덤 프로파일: r ∈ [5, 50]mm, H ∈ [30, 250]mm.
계열: cylinder / cone / bottle / free (연속 랜덤 제어점).
리그 계단 형상은 평가 전용(여기서는 학습 분포만 다룸).
"""
import numpy as np

try:
    from .. import config
except ImportError:
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from v2 import config


def sample_profile(rng: np.random.Generator):
    """랜덤 형상 1개 → (z_grid, r_grid) [m]. 반환 프로파일은 선형보간용 절점."""
    H = rng.uniform(config.H_MIN, config.H_MAX)
    kind = rng.choice(["cylinder", "cone", "bottle", "free"], p=[0.2, 0.2, 0.25, 0.35])

    if kind == "cylinder":
        r0 = rng.uniform(config.R_MIN, config.R_MAX)
        z, r = np.array([0.0, H]), np.array([r0, r0])

    elif kind == "cone":
        rb, rt = rng.uniform(config.R_MIN, config.R_MAX, 2)
        z, r = np.array([0.0, H]), np.array([rb, rt])

    elif kind == "bottle":
        body = rng.uniform(config.R_MIN * 3, config.R_MAX)
        neck = rng.uniform(config.R_MIN, max(config.R_MIN * 1.5, body * 0.5))
        zn = rng.uniform(0.5, 0.85) * H            # 목 시작
        tw = rng.uniform(0.05, 0.15) * H           # 전이 폭
        z = np.linspace(0, H, 50)
        r = np.where(z < zn - tw, body,
             np.where(z > zn + tw, neck,
              body + (neck - body) * 0.5 * (1 - np.cos(np.pi * (z - zn + tw) / (2 * tw)))))

    else:  # free: 랜덤워크 제어점
        n_ctrl = rng.integers(4, 11)
        r = [rng.uniform(config.R_MIN, config.R_MAX)]
        for _ in range(n_ctrl - 1):
            r.append(r[-1] + rng.normal(0, 0.008))
        r = np.clip(r, config.R_MIN, config.R_MAX)
        z = np.linspace(0, H, n_ctrl)

    return np.asarray(z, float), np.asarray(r, float)


def volume_profile(z, r, n=400):
    """누적 부피 곡선 (z_fine, V_cum[m³]) — 사다리꼴 적분."""
    zz = np.linspace(0.0, z[-1], n)
    rr = np.interp(zz, z, r)
    A = np.pi * rr ** 2
    V = np.concatenate([[0.0], np.cumsum(0.5 * (A[:-1] + A[1:]) * np.diff(zz))])
    return zz, V


def slot_labels(z, r):
    """§7 라벨: 25슬롯(10mm 밴드) 평균 단면적의 등가반지름 + 유효 마스크."""
    H = z[-1]
    labels = np.zeros(config.N_SLOTS, dtype=np.float32)
    mask = np.zeros(config.N_SLOTS, dtype=np.float32)
    for i in range(config.N_SLOTS):
        lo, hi = i * config.SLOT_PITCH, (i + 1) * config.SLOT_PITCH
        if lo >= H:
            break
        hi_c = min(hi, H)
        zz = np.linspace(lo, hi_c, 16)
        A_mean = np.mean(np.pi * np.interp(zz, z, r) ** 2)
        labels[i] = np.sqrt(A_mean / np.pi)
        mask[i] = 1.0
    return labels, mask
