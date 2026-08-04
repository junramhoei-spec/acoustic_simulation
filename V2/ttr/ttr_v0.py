"""TTR v0 — 테스트타임 정제 프로토타입 (2026-08-04)

위치: acoustic_simulation/v2/ttr/ttr_v0.py  (프로젝트 루트 자동 인식)

설계 (북극성 2단계 + 리그 ΔL 발견 반영):
  매개변수: H(스칼라), r_slots(25, 10mm 슬롯), delta(리그 유효길이 연장, 입구 반지름 세그먼트)
  초깃값:   NN 전문가 결합(CombinedPredictor) 예측, delta=10mm
  손실:     스텝 간 중앙값 차감 잔차 스펙트럼(100~3200Hz)의 MSE
            (중앙값 차감 = 정적 라인·배경 제거, 모드 궤적만 남김)
            + 평활 정칙화 λ_s·Σ(Δr)²
  물리 앵커: 수위 h(V)를 '현재 형상'에서 미분가능하게 계산 → 모드 궤적 기울기가 단면적을 구속

알려진 한계 (v1에서 개선 예정 — TTR_v0_결과_20260804.md 참고):
  - 원통에서 H와 delta가 퇴화(합 H+δ만 식별) → v1: 세션 공유 δ / 주파수 의존 δ / 0스텝 앵커
  - 잔차 MSE가 좁은 딥 위치 신호를 희석 → v1: 딥 위치 기반 손실
  - NN 초깃값의 지역 최솟값(#20 프로파일 반전) → v1: 다중 초깃값
"""
import os, sys
import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from v2 import config
from v2.forward import tmm_torch as tt

DTYPE = torch.float64
FREQS_FULL = np.linspace(50, 7000, 700)
BAND = (FREQS_FULL >= 100) & (FREQS_FULL <= 3200)
FREQS_T = torch.tensor(FREQS_FULL[BAND], dtype=DTYPE)
SLOT = 0.010
NS = 25

def water_height(vol, areas, H):
    """부피 vol[m³] → 수위[m]. areas(25,) 슬롯 단면적. 미분가능."""
    caps = areas * SLOT
    cum = torch.cumsum(caps, 0)
    cum_lo = torch.cat([torch.zeros(1, dtype=DTYPE), cum[:-1]])
    idx = int(torch.searchsorted(cum.detach(), torch.as_tensor(vol, dtype=DTYPE)).clamp(max=NS-1))
    h = idx * SLOT + (torch.as_tensor(vol, dtype=DTYPE) - cum_lo[idx]) / areas[idx].clamp(min=1e-6)
    return torch.minimum(h, H * 0.98)

def build_profile(h, H, r_slots, delta):
    """수위 h부터 입구 H까지 공기기둥 프로파일 (+delta 연장). z=0이 수면."""
    n = 60
    frac = torch.linspace(0.0, 1.0, n, dtype=DTYPE)
    z_abs = h + (H - h) * frac
    idx = (z_abs.detach() / SLOT).long().clamp(0, NS - 1)
    r = r_slots[idx]
    z = z_abs - h
    z_ext = torch.stack([z[-1] + 1e-9, z[-1] + delta.clamp(min=1e-4)])
    r_ext = torch.stack([r[-1], r[-1]])
    return torch.cat([z, z_ext]), torch.cat([r, r_ext])

def sim_sequence(H, r_slots, delta, v_cum):
    specs = []
    areas = np.pi * r_slots ** 2
    for v in v_cum:
        h = water_height(float(v), areas, H)
        z, r = build_profile(h, H, r_slots, delta)
        _, s = tt.dip_spectrum_t(z, r, FREQS_T)
        specs.append(s)
    return torch.stack(specs)

def resid(spec):
    """스텝 간 중앙값 차감 (정적 성분 제거)."""
    med = spec.median(dim=0).values
    return spec - med[None, :]

def ttr_refine(spec_meas, v_cum, H0_mm, r0_mm, iters=150, lr=2e-3,
               lam_smooth=3.0, delta0_mm=10.0, w_step0=1.0, verbose=True):
    """spec_meas: (S,700) log10|H| 실측(생성 그리드 700bins), v_cum: (S,) [m³].
    반환: H_mm, r_mm(25), delta_mm, loss 이력."""
    S = len(spec_meas)
    meas = torch.tensor(np.asarray(spec_meas, np.float64)[:, BAND], dtype=DTYPE)
    meas_r = resid(meas)
    w = torch.ones(S, dtype=DTYPE); w[0] = w_step0
    w = w / w.sum() * S

    def inv_sig(x): return np.log(x / (1 - x))
    H_n = torch.tensor(inv_sig(np.clip((H0_mm/1000 - config.H_MIN)/(config.H_MAX-config.H_MIN), 0.02, 0.98)),
                       dtype=DTYPE, requires_grad=True)
    r_n = torch.tensor(inv_sig(np.clip((np.asarray(r0_mm)/1000 - config.R_MIN)/(config.R_MAX-config.R_MIN), 0.02, 0.98)),
                       dtype=DTYPE, requires_grad=True)
    d_n = torch.tensor(inv_sig(np.clip(delta0_mm/30.0, 0.02, 0.98)), dtype=DTYPE, requires_grad=True)

    opt = torch.optim.Adam([{'params': [H_n], 'lr': lr},
                            {'params': [r_n], 'lr': lr*2},
                            {'params': [d_n], 'lr': lr*2}])
    hist = []
    for it in range(iters):
        H = (config.H_MIN + torch.sigmoid(H_n)*(config.H_MAX-config.H_MIN))
        r_slots = (config.R_MIN + torch.sigmoid(r_n)*(config.R_MAX-config.R_MIN))
        delta = torch.sigmoid(d_n) * 0.030
        sim = sim_sequence(H, r_slots, delta, v_cum)
        per_step = ((resid(sim) - meas_r) ** 2).mean(dim=1)
        loss_fit = (w * per_step).mean()
        loss = loss_fit + lam_smooth * ((r_slots[1:] - r_slots[:-1]) ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
        hist.append(float(loss_fit.detach()))
        if verbose and (it % 25 == 0 or it == iters-1):
            print(f"  it{it:3d} fit={hist[-1]:.5f} H={float(H)*1000:6.1f} δ={float(delta)*1000:5.1f}", flush=True)
    H = float(config.H_MIN + torch.sigmoid(H_n)*(config.H_MAX-config.H_MIN)) * 1000
    r = (config.R_MIN + torch.sigmoid(r_n).detach().numpy()*(config.R_MAX-config.R_MIN)) * 1000
    d = float(torch.sigmoid(d_n)) * 30.0
    return H, r, d, hist
