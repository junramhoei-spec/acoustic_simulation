# -*- coding: utf-8 -*-
"""TTR v1 — 다중 초깃값 + 잔차 기준 선별 (+옵션: 딥 위치 앵커) (2026-08-04)

v0 대비 확정 설계 변경:
  1. 다중 초깃값: NN 예측 / 프로파일 상하 반전 / 등가 원통 3곳에서 짧은 선별
     최적화(iters_screen) 후 본 최적화. → 지역 최솟값 대응.
  2. 초깃값 선별 기준은 'v0 잔차 MSE'(전 스펙트럼): 딥 위치 손실은 스텝이 적을 때
     희소해서 오답 형상(#15 반전)도 낮게 나옴을 실증 — 선별은 반드시 잔차 기준.

옵션으로 보존(기본 OFF, lam_dip=0):
  딥 위치 기반 미분가능 손실 — 실측 잔차에서 딥 위치 추출(1회) 후 각 딥 주변 창에서
  시뮬레이션 잔차의 soft-argmin 위치 오차를 손실로. 50mL·4스텝 데이터 어블레이션에서
  전면 적용(#16/#13 후퇴)·0스텝 한정 적용 모두 잔차 단독보다 나빠 기본 비활성.
  스텝이 촘촘한 데이터(10mL 재측정)에서 lam_dip>0 + dip_scope로 재평가 예정.

유지: δ(리그 유효길이 연장) 자유 매개변수, 시그모이드 정규화 공간 최적화,
      r 평활 정칙화, 잔차 MSE 손실(lam_res=1.0 — v0 손실이 본체).

공통 시그니처: ttr_refine(spec(S,700), v_cum, H0_mm, r0_mm, verbose, progress_cb, **opts)
반환: (H_mm, r_mm(25,), delta_mm, loss_hist)
"""
import os, sys
import numpy as np
import torch
from scipy.signal import find_peaks

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from v2 import config
from v2.forward import tmm_torch as tt

DTYPE = torch.float64
FREQS_FULL = np.linspace(50, 7000, 700)
BAND = (FREQS_FULL >= 100) & (FREQS_FULL <= 3200)
FREQS_B = FREQS_FULL[BAND]
FREQS_T = torch.tensor(FREQS_B, dtype=DTYPE)
SLOT = 0.010
NS = 25


# ── v0과 동일한 순방향 구성요소 ─────────────────────────────
def water_height(vol, areas, H):
    caps = areas * SLOT
    cum = torch.cumsum(caps, 0)
    cum_lo = torch.cat([torch.zeros(1, dtype=DTYPE), cum[:-1]])
    idx = int(torch.searchsorted(cum.detach(), torch.as_tensor(vol, dtype=DTYPE)).clamp(max=NS - 1))
    h = idx * SLOT + (torch.as_tensor(vol, dtype=DTYPE) - cum_lo[idx]) / areas[idx].clamp(min=1e-6)
    return torch.minimum(h, H * 0.98)


def build_profile(h, H, r_slots, delta):
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
    med = spec.median(dim=0).values
    return spec - med[None, :]


# ── 실측 딥 추출 (비미분, 1회) ──────────────────────────────
def extract_dips(meas_r_np, prom_th, max_dips):
    """meas_r_np: (S, F_band) 잔차. 반환: [(step, i_center, f_meas, prominence)]."""
    dips = []
    for s in range(meas_r_np.shape[0]):
        idx, props = find_peaks(-meas_r_np[s], prominence=prom_th)
        if len(idx) == 0:
            continue
        order = np.argsort(props["prominences"])[::-1][:max_dips]
        for j in order:
            dips.append((s, int(idx[j]), float(FREQS_B[idx[j]]),
                         float(props["prominences"][j])))
    return dips


# ── 최적화 코어 ──────────────────────────────────────────────
def _inv_sig(x):
    return np.log(x / (1 - x))


def _make_params(H0_mm, r0_mm, delta0_mm):
    H_n = torch.tensor(_inv_sig(np.clip((H0_mm / 1000 - config.H_MIN) / (config.H_MAX - config.H_MIN), 0.02, 0.98)),
                       dtype=DTYPE, requires_grad=True)
    r_n = torch.tensor(_inv_sig(np.clip((np.asarray(r0_mm, np.float64) / 1000 - config.R_MIN) / (config.R_MAX - config.R_MIN), 0.02, 0.98)),
                       dtype=DTYPE, requires_grad=True)
    d_n = torch.tensor(_inv_sig(np.clip(delta0_mm / 30.0, 0.02, 0.98)), dtype=DTYPE, requires_grad=True)
    return H_n, r_n, d_n


def _decode(H_n, r_n, d_n):
    H = config.H_MIN + torch.sigmoid(H_n) * (config.H_MAX - config.H_MIN)
    r = config.R_MIN + torch.sigmoid(r_n) * (config.R_MAX - config.R_MIN)
    d = torch.sigmoid(d_n) * 0.030
    return H, r, d


def _eval_res(params, v_cum, meas_r):
    """v0 손실(잔차 MSE)로 평가 — 초깃값 선별 기준 (검증된 전 스펙트럼 구속)."""
    H_n, r_n, d_n = params
    with torch.no_grad():
        H, r_slots, delta = _decode(H_n, r_n, d_n)
        sim_r = resid(sim_sequence(H, r_slots, delta, v_cum))
        return float(((sim_r - meas_r) ** 2).mean())


def _optimize(params, v_cum, meas_r, dips, dip_w, half_w, opts, n_iters, tick):
    """params=(H_n,r_n,d_n) 제자리 최적화. 반환: fit 손실 이력(딥+잔차, 정칙화 제외)."""
    H_n, r_n, d_n = params
    lr = opts["lr"]
    opt = torch.optim.Adam([{'params': [H_n], 'lr': lr},
                            {'params': [r_n], 'lr': lr * 2},
                            {'params': [d_n], 'lr': lr * 2}])
    beta = opts["beta"]
    lam_res, lam_dip, lam_smooth = opts["lam_res"], opts["lam_dip"], opts["lam_smooth"]
    F = meas_r.shape[1]
    hist = []
    for _ in range(n_iters):
        H, r_slots, delta = _decode(H_n, r_n, d_n)
        sim = sim_sequence(H, r_slots, delta, v_cum)
        sim_r = resid(sim)

        # 딥 위치 손실: 실측 딥 주변 창에서 sim 잔차의 soft-argmin 위치와 비교
        loss_dip = torch.zeros((), dtype=DTYPE)
        for (s, ic, f_meas, _p), w in zip(dips, dip_w):
            i0, i1 = max(0, ic - half_w), min(F, ic + half_w + 1)
            seg = sim_r[s, i0:i1]
            p = torch.softmax(-beta * seg, dim=0)
            f_hat = (p * FREQS_T[i0:i1]).sum()
            loss_dip = loss_dip + w * ((f_hat - f_meas) * 1e-3) ** 2
        loss_dip = loss_dip / max(len(dips), 1)

        loss_res = ((sim_r - meas_r) ** 2).mean()
        loss_fit = lam_dip * loss_dip + lam_res * loss_res
        loss = loss_fit + lam_smooth * ((r_slots[1:] - r_slots[:-1]) ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
        hist.append(float(loss_fit.detach()))
        tick()
    return hist


def ttr_refine(spec_meas, v_cum, H0_mm, r0_mm, iters=120, iters_screen=40, lr=2e-3,
               lam_smooth=3.0, lam_res=1.0, lam_dip=0.0, beta=30.0, win_hz=250.0,
               prom_th=0.12, max_dips=6, w_step0=3.0, delta0_mm=10.0,
               dip_scope="step0", verbose=True, progress_cb=None):
    """spec_meas: (S,700) log10|H| 실측(생성 그리드), v_cum: (S,) [m³].
    반환: H_mm, r_mm(25), delta_mm, loss 이력(본 최적화 구간).
    progress_cb(done, total): 선별 3회 + 본 최적화 전체 기준."""
    meas_np = np.asarray(spec_meas, np.float64)[:, BAND]
    meas_r_np = meas_np - np.median(meas_np, axis=0, keepdims=True)
    meas_r = torch.tensor(meas_r_np, dtype=DTYPE)

    # 실측 딥 추출 + 가중치 (0스텝 앵커: w_step0 배). lam_dip=0이면 딥 손실 미사용.
    dips = []
    dip_w = torch.zeros(0, dtype=DTYPE)
    if lam_dip > 0:
        dips = extract_dips(meas_r_np, prom_th, max_dips)
        if dip_scope == "step0":   # 딥 손실을 0스텝(바닥 앵커)에만 한정
            dips = [d for d in dips if d[0] == 0]
        if not dips:
            raise RuntimeError("실측 잔차에서 딥을 찾지 못함 (prom_th를 낮춰보세요)")
        w = np.array([p for (_s, _i, _f, p) in dips], np.float64)
        w = w / w.mean()
        w = w * np.array([w_step0 if s == 0 else 1.0 for (s, _i, _f, _p) in dips])
        dip_w = torch.tensor(w / w.mean(), dtype=DTYPE)

    df = FREQS_B[1] - FREQS_B[0]
    half_w = max(3, int(round(win_hz / df)))
    opts = dict(lr=lr, beta=beta, lam_res=lam_res, lam_dip=lam_dip, lam_smooth=lam_smooth)

    # 다중 초깃값: NN / 상하 반전 / 등가 원통 (유효 슬롯 구간만)
    r0 = np.asarray(r0_mm, np.float64)
    n_valid = int(np.clip(np.ceil(H0_mm / 10.0), 1, NS))
    r_flip = r0.copy(); r_flip[:n_valid] = r0[:n_valid][::-1]
    r_cyl = r0.copy(); r_cyl[:n_valid] = r0[:n_valid].mean()
    inits = [("nn", r0), ("flip", r_flip), ("cyl", r_cyl)]

    total = len(inits) * iters_screen + iters
    done = [0]
    def tick():
        done[0] += 1
        if progress_cb is not None:
            progress_cb(done[0], total)

    # 1단계: 선별 — 짧은 최적화 후 'v0 잔차 MSE'로 초깃값 선택.
    # (딥 손실은 스텝이 적을 때 희소해 오답 형상도 낮게 나올 수 있음(#15에서 실증).
    #  선별만은 전 스펙트럼을 쓰는 검증된 v0 기준으로 판정)
    best = None
    for name, r_init in inits:
        params = _make_params(H0_mm, r_init, delta0_mm)
        hist_s = _optimize(params, v_cum, meas_r, dips, dip_w, half_w, opts, iters_screen, tick)
        res_m = _eval_res(params, v_cum, meas_r)
        if verbose:
            print(f"  [선별] init={name:4s} fit={hist_s[-1]:.5f} res={res_m:.5f}", flush=True)
        if best is None or res_m < best[1]:
            best = (name, res_m, params)

    # 2단계: 본 최적화 (선별 승자 이어서)
    name, _, params = best
    if verbose:
        print(f"  [본 최적화] init={name} 채택", flush=True)
    hist = _optimize(params, v_cum, meas_r, dips, dip_w, half_w, opts, iters, tick)

    H_n, r_n, d_n = params
    with torch.no_grad():
        H, r, d = _decode(H_n, r_n, d_n)
    return float(H) * 1000, r.numpy() * 1000, float(d) * 1000, hist
