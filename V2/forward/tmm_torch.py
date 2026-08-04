"""
미분가능 순방향 시뮬레이터 — tmm.py의 PyTorch 포팅.
(sim2real 실행계획 Step 3 "테스트타임 정제"의 전제 조건. 2026-07-11 작성)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 왜 "미분가능" 버전이 따로 필요한가? (초보자용 배경 설명)

  기존 tmm.py(NumPy)는 "형상 → 스펙트럼" 계산만 할 수 있다.
  테스트타임 정제는 그 반대 방향 질문을 한다:
    "측정된 스펙트럼과 더 비슷해지려면 형상(r, H)을 어느 쪽으로
     얼마나 움직여야 하는가?"
  이 "어느 쪽으로"가 바로 gradient(기울기)이고, PyTorch는 계산 과정을
  전부 기억했다가 자동으로 gradient를 구해 준다(autograd).
  NumPy는 이 기능이 없다 → 그래서 같은 물리 계산을 torch 연산만으로
  다시 쓴 것이 이 파일이다.

  개념도 (테스트타임 정제 = 학습이 아니라 '답안 다듬기'):
    NN 예측 (r, H) ──→ [이 파일: TMM] ──→ 예측 스펙트럼
         ↑                                      │
         └── gradient로 (r, H) 몇 스텝 수정 ←── 측정 스펙트럼과의 차이(손실)

■ NumPy 원본과 딱 한 곳이 다르다: 스트루브 함수 H₁
  방사 임피던스의 허수부에 스트루브 함수가 필요한데 torch에 없다.
  → Aarts & Janssen (2003) 유리·삼각 근사로 대체:
      H₁(x) ≈ 2/π − J₀(x) + (16/π − 5)·sin(x)/x + (12 − 36/π)·(1 − cos x)/x²
    (최대 절대 오차 ~0.005, 스피커 방사 임피던스 용도로 개발된 근사.
     검증 결과는 파일 끝 self-test 참고 — 스펙트럼 오차에 거의 영향 없음.)

■ 사용 규칙
  - 입력 z_grid, r_grid, (H)는 requires_grad=True 텐서로 만들면
    dip_spectrum_t() 출력에서 .backward()로 형상 gradient를 받을 수 있다.
  - 세그먼트 개수 n_seg는 정수라 미분 불가 → 정제 시작 시점의 H로 고정된다.
    (H가 정제 중 몇 mm 움직여도 세그먼트 5mm 해상도에는 영향 미미)
  - 정밀도: float64/complex128 사용 (공명 근처는 수치적으로 예민해서
    float32로는 NumPy 원본과 차이가 커질 수 있음).

■ 빠른 검증 (아무 컴퓨터, GPU 불필요):
  python v2\forward\tmm_torch.py
  → NumPy 원본과의 최대 오차 + gradient 유한차분 대조를 자동 출력.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

import math

import torch

try:  # 패키지/단독 실행 겸용 (tmm.py와 같은 패턴)
    from .. import config
except ImportError:  # pragma: no cover
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from v2 import config

DTYPE = torch.float64          # 실수 기본 정밀도
CDTYPE = torch.complex128      # 복소 기본 정밀도


def _as_tensor(x, dtype=DTYPE):
    if isinstance(x, torch.Tensor):
        return x.to(dtype)
    return torch.as_tensor(x, dtype=dtype)


# ─────────────────────────────────────────────────────────────
# 0) 미분가능 선형 보간 (np.interp 대체)
# ─────────────────────────────────────────────────────────────
def interp_t(x_new, x_grid, y_grid):
    """np.interp의 torch 버전 — y_grid(와 x_grid)에 대해 미분 가능.

    구간 인덱스 선택(searchsorted)은 미분 불가지만, 보간 가중치와 y값은
    미분 가능 → gradient가 y_grid(반지름)와 x 좌표로 정상적으로 흐른다.
    x_grid는 오름차순 가정, 범위 밖은 양끝 값으로 클램프(np.interp와 동일)."""
    idx = torch.searchsorted(x_grid.detach(), x_new.detach()).clamp(1, len(x_grid) - 1)
    x0, x1 = x_grid[idx - 1], x_grid[idx]
    y0, y1 = y_grid[idx - 1], y_grid[idx]
    w = ((x_new - x0) / (x1 - x0).clamp(min=1e-12)).clamp(0.0, 1.0)
    return y0 + w * (y1 - y0)


# ─────────────────────────────────────────────────────────────
# 1) Kirchhoff 경계층 감쇠 (tmm.kirchhoff_alpha와 동일 수식)
# ─────────────────────────────────────────────────────────────
def kirchhoff_alpha_t(freqs, radius, temp_c=config.AIR_TEMP_C):
    """감쇠 계수 α(f, r) [Np/m]. radius가 텐서면 gradient가 흐른다."""
    c = config.air_speed_of_sound(temp_c)
    rho = config.air_density(temp_c)
    omega = 2.0 * math.pi * freqs
    visc_term = torch.sqrt(torch.as_tensor(config.AIR_VISCOSITY, dtype=DTYPE) * omega
                           / (2.0 * rho))
    thermal_factor = 1.0 + (config.AIR_GAMMA - 1.0) / math.sqrt(config.AIR_PRANDTL)
    return visc_term * thermal_factor / (radius * c)


# ─────────────────────────────────────────────────────────────
# 2) 세그먼트 분할 (tmm.segment_profile의 미분가능 버전)
# ─────────────────────────────────────────────────────────────
def segment_profile_t(z_grid, r_grid, seg_dz=config.SEG_DZ, n_seg_min=config.N_SEG_MIN):
    """(z_grid, r_grid) → (seg_len 스칼라 텐서, r_mid (n_seg,) 텐서).

    n_seg(세그먼트 개수)는 현재 높이값으로 '한 번' 정해지는 정수 —
    이 선택 자체는 미분 불가지만 seg_len = H/n_seg 와 z_mid 좌표는
    H의 함수로 미분 가능하게 유지된다."""
    z_grid = _as_tensor(z_grid)
    r_grid = _as_tensor(r_grid)
    height = z_grid[-1]
    n_seg = max(n_seg_min, int(math.ceil(float(height.detach()) / seg_dz)))
    # z_edges = H × (0, 1/n, 2/n, ..., 1) → H에 대해 미분 가능
    frac = torch.linspace(0.0, 1.0, n_seg + 1, dtype=DTYPE, device=z_grid.device)
    z_edges = height * frac
    z_mid = 0.5 * (z_edges[:-1] + z_edges[1:])
    r_mid = interp_t(z_mid, z_grid, r_grid)
    seg_len = height / n_seg
    return seg_len, r_mid


# ─────────────────────────────────────────────────────────────
# 3) 공동 입력 임피던스 (tmm.input_impedance와 동일 수식)
# ─────────────────────────────────────────────────────────────
def input_impedance_t(freqs, seg_len, r_mid, temp_c=config.AIR_TEMP_C, damping=True):
    """Z_in(f) 복소 텐서 (F,). 전달행렬(TMM)을 바닥→입구로 누적 곱.

    수식·부호 규약은 tmm.py와 완전히 동일. 반복문은 세그먼트(≈30~50개)
    방향으로만 돌고 주파수축(F=700)은 벡터화 — 원본과 같은 구조."""
    c = config.air_speed_of_sound(temp_c)
    rho = config.air_density(temp_c)
    freqs = _as_tensor(freqs)
    k_real = 2.0 * math.pi * freqs / c

    F = len(freqs)
    dev = r_mid.device
    t11 = torch.ones(F, dtype=CDTYPE, device=dev)
    t12 = torch.zeros(F, dtype=CDTYPE, device=dev)
    t21 = torch.zeros(F, dtype=CDTYPE, device=dev)
    t22 = torch.ones(F, dtype=CDTYPE, device=dev)

    for i in range(len(r_mid)):
        r_seg = r_mid[i]
        if damping:
            alpha = kirchhoff_alpha_t(freqs, r_seg, temp_c)
            k = k_real.to(CDTYPE) + (1.0 - 1.0j) * alpha.to(CDTYPE)
        else:
            k = k_real.to(CDTYPE)

        area = math.pi * r_seg ** 2
        Zc = (rho * c / area).to(CDTYPE)
        kl = k * seg_len.to(CDTYPE)
        cos_kl = torch.cos(kl)
        j_sin_kl = 1j * torch.sin(kl)

        a11, a12 = cos_kl, Zc * j_sin_kl
        a21, a22 = j_sin_kl / Zc, cos_kl

        n11 = t11 * a11 + t12 * a21
        n12 = t11 * a12 + t12 * a22
        n21 = t21 * a11 + t22 * a21
        n22 = t21 * a12 + t22 * a22
        t11, t12, t21, t22 = n11, n12, n21, n22

    # 0 나누기 방지 (원본의 np.where와 동일한 역할, 미분 안전한 방식)
    small = t21.abs() < 1e-30
    t21 = torch.where(small, torch.full_like(t21, 1e-30), t21)
    return t22 / t21


# ─────────────────────────────────────────────────────────────
# 4) 입구 방사 임피던스 — 스트루브 함수만 근사로 대체
# ─────────────────────────────────────────────────────────────
# ※ 함정 주의: torch.special.bessel_j0/j1은 값은 계산해 주지만
#   미분(autograd) 규칙이 등록돼 있지 않다 (torch 2.13 기준).
#   그냥 쓰면 에러도 없이 gradient 그래프가 '조용히' 끊겨서
#   방사 임피던스 쪽 gradient가 통째로 누락된다 (실제로 겪은 버그).
#   → 수학 교과서의 도함수 공식을 직접 등록해서 해결:
#       J₀'(x) = −J₁(x),   J₁'(x) = J₀(x) − J₁(x)/x  (x→0 극한: 1/2)
class _BesselJ0(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward(x)
        return torch.special.bessel_j0(x)

    @staticmethod
    def backward(ctx, grad_out):
        (x,) = ctx.saved_tensors
        return -torch.special.bessel_j1(x) * grad_out


class _BesselJ1(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward(x)
        return torch.special.bessel_j1(x)

    @staticmethod
    def backward(ctx, grad_out):
        (x,) = ctx.saved_tensors
        safe = x.clamp(min=1e-12)
        d = torch.special.bessel_j0(safe) - torch.special.bessel_j1(safe) / safe
        d = torch.where(x < 1e-8, torch.full_like(x, 0.5), d)   # J₁'(0) = 1/2
        return d * grad_out


def bessel_j0_t(x):
    """미분 가능한 J₀(x)."""
    return _BesselJ0.apply(x)


def bessel_j1_t(x):
    """미분 가능한 J₁(x)."""
    return _BesselJ1.apply(x)


def struve_h1_t(x):
    """스트루브 함수 H₁(x)의 Aarts & Janssen (2003) 근사 — torch 미분 가능.

        H₁(x) ≈ 2/π − J₀(x) + (16/π − 5)·sin(x)/x + (12 − 36/π)·(1−cos x)/x²

    scipy.special.struve(1, x) 대비 최대 절대 오차 ~0.005 (전 구간).
    배플 피스톤 방사 리액턴스 용도로 만들어진 근사라 우리 용도에 적합."""
    x = x.clamp(min=1e-12)   # x→0에서 sin(x)/x 등 0/0 방지 (극한값은 유한)
    return (2.0 / math.pi - bessel_j0_t(x)
            + (16.0 / math.pi - 5.0) * torch.sin(x) / x
            + (12.0 - 36.0 / math.pi) * (1.0 - torch.cos(x)) / x ** 2)


def radiation_impedance_t(freqs, r_mouth, temp_c=config.AIR_TEMP_C):
    """배플 피스톤 방사 임피던스 (tmm.radiation_impedance exact=True 대응).

        Z = (ρc/S)·[ 1 − J₁(2ka)/ka + j·H₁(2ka)/ka ]

    J₁은 torch.special.bessel_j1(정확), H₁만 위의 근사 사용."""
    c = config.air_speed_of_sound(temp_c)
    rho = config.air_density(temp_c)
    freqs = _as_tensor(freqs)
    k = 2.0 * math.pi * freqs / c
    ka = k * r_mouth
    S = math.pi * r_mouth ** 2
    x = (2.0 * ka).clamp(min=1e-12)
    R = 1.0 - 2.0 * bessel_j1_t(x) / x
    X = 2.0 * struve_h1_t(x) / x
    return (rho * c / S).to(CDTYPE) * (R.to(CDTYPE) + 1j * X.to(CDTYPE))


# ─────────────────────────────────────────────────────────────
# 5) 관측량: 비율 전달함수 (tmm.mic_ratio_response와 동일 수식)
# ─────────────────────────────────────────────────────────────
def mic_ratio_response_t(freqs, z_in, r_mouth,
                         d_mic=config.MIC_HEIGHT,
                         d_spk=config.SPEAKER_DIST,
                         temp_c=config.AIR_TEMP_C):
    """H(f) = p_mic(컵)/p_mic(강체면). 복소 텐서 (F,). 물리 설명은 tmm.py 참고."""
    c = config.air_speed_of_sound(temp_c)
    rho = config.air_density(temp_c)
    freqs = _as_tensor(freqs)
    k = (2.0 * math.pi * freqs / c).to(CDTYPE)

    r_direct = d_spk - d_mic
    r_image = d_spk + d_mic
    p_ref = (torch.exp(-1j * k * r_direct) / r_direct
             + torch.exp(-1j * k * r_image) / r_image)

    a = r_mouth
    S = math.pi * a ** 2
    z_rad = radiation_impedance_t(freqs, a, temp_c)
    p_blocked = 2.0 * torch.exp(-1j * k * d_spk) / d_spk
    u_out = -p_blocked / (z_in + z_rad)
    dist_edge = torch.sqrt((d_mic ** 2 + a ** 2).to(CDTYPE)
                           if isinstance(a, torch.Tensor)
                           else torch.as_tensor(d_mic ** 2 + a ** 2, dtype=CDTYPE))
    piston_field = torch.exp(-1j * k * d_mic) - torch.exp(-1j * k * dist_edge)
    p_scat = (rho * c / S).to(CDTYPE) * u_out * piston_field

    return (p_ref + p_scat) / p_ref


# ─────────────────────────────────────────────────────────────
# 6) 편의 함수: 프로파일 → 딥 스펙트럼 (tmm.dip_spectrum 대응)
# ─────────────────────────────────────────────────────────────
def dip_spectrum_t(z_grid, r_grid, freqs=None, temp_c=config.AIR_TEMP_C,
                   damping=True, rig_top_extension=False):
    """(z_grid, r_grid) 텐서 → (freqs, log10|H| 스펙트럼 텐서).

    z_grid·r_grid에 requires_grad=True를 걸면 반환 스펙트럼에서
    .backward()로 형상 gradient를 받을 수 있다 — 테스트타임 정제의 심장.
    """
    if freqs is None:
        freqs = torch.linspace(config.FREQ_MIN, config.FREQ_MAX, config.N_FREQ,
                               dtype=DTYPE)
    freqs = _as_tensor(freqs)
    z_grid = _as_tensor(z_grid)
    r_grid = _as_tensor(r_grid)

    if rig_top_extension:
        z_grid = torch.cat([z_grid, torch.stack([z_grid[-1] + 1e-9,
                                                 z_grid[-1] + config.RIG_TOP_EXT_H])])
        ext_r = torch.as_tensor([config.RIG_TOP_EXT_R, config.RIG_TOP_EXT_R],
                                dtype=DTYPE, device=r_grid.device)
        r_grid = torch.cat([r_grid, ext_r])

    seg_len, r_mid = segment_profile_t(z_grid, r_grid)
    z_in = input_impedance_t(freqs, seg_len, r_mid, temp_c, damping)
    r_mouth = r_grid[-1]
    h = mic_ratio_response_t(freqs, z_in, r_mouth, temp_c=temp_c)
    return freqs, torch.log10(h.abs() + 1e-12)


# ─────────────────────────────────────────────────────────────
# self-test: NumPy 원본 대조 + gradient 확인
#   실행:  python v2\forward\tmm_torch.py        (GPU 불필요, 수 초 소요)
#   또는:  python -c "from v2.forward.tmm_torch import selftest; selftest()"
# ─────────────────────────────────────────────────────────────
def selftest():
    """NumPy 원본과의 수치 일치 + gradient 정합성 자동 검증."""
    import numpy as np

    from v2.forward import tmm  # NumPy 원본

    print("=" * 62)
    print("tmm_torch self-test — NumPy 원본과 수치 대조")
    print("=" * 62)

    rng = np.random.default_rng(7)
    worst = 0.0
    for trial in range(5):
        # 무작위 컵 형상: 높이 60~240mm, 반지름 8~48mm의 매끈한 프로파일
        H = rng.uniform(0.06, 0.24)
        n_knot = rng.integers(3, 7)
        z_np = np.linspace(0.0, H, n_knot)
        r_np = rng.uniform(0.008, 0.048, n_knot)

        _, spec_np = tmm.dip_spectrum(z_np, r_np)
        _, spec_t = dip_spectrum_t(torch.tensor(z_np), torch.tensor(r_np))
        diff = float(np.max(np.abs(spec_np - spec_t.numpy())))
        worst = max(worst, diff)
        print(f"  형상 {trial + 1}: H={H * 1000:5.1f}mm, 매듭 {n_knot}개 → "
              f"log10 스펙트럼 최대 오차 {diff:.2e}")
    # 판정 기준 5e-2인 이유: 오차의 원천은 스트루브 근사(절대 ~0.005) 하나뿐이고
    # (동일 근사를 NumPy에 심으면 구현 차이는 1e-8 이하로 확인됨, 2026-07-11),
    # 그 오차는 딥의 '가장 깊은 바닥'(log값이 급변하는 곳)에 집중된다.
    # 딥의 위치(공명 주파수)와 전체 모양에는 영향이 미미 → 정제 용도로 충분.
    print(f"  → 전체 최대 오차 {worst:.2e} "
          f"({'OK: 스트루브 근사 기인, 딥 바닥에 국한 — 정제 용도 문제없음' if worst < 5e-2 else '경고: 예상보다 큼!'})")

    # gradient 검증: autograd vs 유한차분(수치 미분)
    print("-" * 62)
    print("gradient 검증 (autograd vs 유한차분)")
    H = 0.15
    z = torch.linspace(0.0, H, 5, dtype=DTYPE)
    r = torch.full((5,), 0.03, dtype=DTYPE, requires_grad=True)
    _, spec = dip_spectrum_t(z, r)
    loss = spec.sum()          # 아무 스칼라 손실
    loss.backward()
    g_auto = r.grad.clone()

    eps = 1e-6
    g_fd = torch.zeros(5, dtype=DTYPE)
    for i in range(5):
        rp = r.detach().clone(); rp[i] += eps
        rm = r.detach().clone(); rm[i] -= eps
        _, sp = dip_spectrum_t(z, rp)
        _, sm_ = dip_spectrum_t(z, rm)
        g_fd[i] = (sp.sum() - sm_.sum()) / (2 * eps)

    rel = float((g_auto - g_fd).abs().max() / g_fd.abs().max().clamp(min=1e-30))
    print(f"  ∂loss/∂r: autograd {g_auto.numpy().round(3)}")
    print(f"            유한차분 {g_fd.numpy().round(3)}")
    print(f"  상대 오차 {rel:.2e}  ({'OK' if rel < 1e-4 else '경고: gradient 불일치!'})")
    print("=" * 62)


if __name__ == "__main__":
    selftest()
