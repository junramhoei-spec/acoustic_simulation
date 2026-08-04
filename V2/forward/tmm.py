"""
순방향 시뮬레이터 v2 — 1D TMM + Kirchhoff 경계층 감쇠 + 입구 딥 관측 모델(마이크 B).
설계 근거: docs/연구_설계_프레임_v1.md §5

구성 (전부 주파수축 벡터화, 기본 연산만 사용 → 추후 torch 포팅(PINN) 용이):
  1) kirchhoff_alpha()      : 점성·열 경계층 감쇠 계수 α(f, r)  [Np/m]
  2) input_impedance()      : 폐(바닥)-개(입구) 공동의 입구 입력 임피던스 Z_in(f)
  3) radiation_impedance()  : 입구 방사 임피던스 Z_rad(f)
  4) mic_ratio_response()   : 관측량 = "컵 있음 / 컵 없음(강체면)" 비율 전달함수 H(f)
                              → 공명에서 딥(dip)

물리 요약 (마이크 B 모델):
  마이크(입구 위 d_m)에 오는 소리 = ① 스피커 직접음 + ② 강체 기준면 반사(이미지)
  + ③ 입구가 흡수했다 되쏘는 재방사(배플 피스톤).
  컵 없음(피스톤 최상단 = 강체 평면) 기준은 ①+②만 존재.
  비율 H = (①+②+③)/(①+②). 공명에서 |Z_in+Z_rad| 리액턴스 소멸 → ③ 최대 → 상쇄 → 딥.
  스피커·마이크·룸 특성은 비율에서 약분(§5 관측량 결정).

부호 규약: 시간 인자 e^{+jωt}, 전파 e^{-jkz}. 감쇠는 k = ω/c + (1-j)α.
"""
from __future__ import annotations

import numpy as np

try:  # 패키지/단독 실행 겸용
    from .. import config
except ImportError:  # pragma: no cover
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from v2 import config


# ─────────────────────────────────────────────────────────────
# 1) Kirchhoff 경계층 감쇠 (§5 결정: 튜닝 파라미터 없음)
# ─────────────────────────────────────────────────────────────
def kirchhoff_alpha(freqs, radius, temp_c=config.AIR_TEMP_C):
    """
    넓은 관(경계층 << r) 근사의 고전 Kirchhoff 감쇠 계수 [Np/m].

        α = (1 / (r·c)) · sqrt(μ·ω / (2·ρ)) · (1 + (γ-1)/sqrt(Pr))

    점성 손실 + 열전도 손실. 모든 상수는 공기 물성(문헌값).
    """
    c = config.air_speed_of_sound(temp_c)
    rho = config.air_density(temp_c)
    omega = 2.0 * np.pi * np.asarray(freqs, dtype=float)
    visc_term = np.sqrt(config.AIR_VISCOSITY * omega / (2.0 * rho))
    thermal_factor = 1.0 + (config.AIR_GAMMA - 1.0) / np.sqrt(config.AIR_PRANDTL)
    return visc_term * thermal_factor / (np.asarray(radius) * c)


# ─────────────────────────────────────────────────────────────
# 2) 공동 입력 임피던스 (TMM, 주파수 벡터화)
# ─────────────────────────────────────────────────────────────
def segment_profile(z_grid, r_grid, seg_dz=config.SEG_DZ, n_seg_min=config.N_SEG_MIN):
    """
    연속 프로파일 (z_grid, r_grid) → TMM 세그먼트 (길이, 중점 반지름) 배열.
    z_grid[0]=0(바닥, 폐), z_grid[-1]=H(입구, 개). r은 선형 보간.
    """
    height = float(z_grid[-1])
    n_seg = max(n_seg_min, int(np.ceil(height / seg_dz)))
    z_edges = np.linspace(0.0, height, n_seg + 1)
    z_mid = 0.5 * (z_edges[:-1] + z_edges[1:])
    r_mid = np.interp(z_mid, z_grid, r_grid)
    seg_len = height / n_seg
    return seg_len, r_mid


def input_impedance(freqs, seg_len, r_mid, temp_c=config.AIR_TEMP_C, damping=True):
    """
    바닥 폐쇄(U=0) 공동을 입구에서 들여다본 입력 임피던스 Z_in(f). (복소, shape=(F,))

    관례: [p_bottom, U_bottom]^T = T_total · [p_mouth, U_mouth]^T,
          U_bottom = 0  →  Z_in = p_mouth / U_mouth(안쪽 양) = T22 / T21.
    감쇠 시 세그먼트별 국소 반지름으로 α를 계산해 k를 복소화.
    """
    c = config.air_speed_of_sound(temp_c)
    rho = config.air_density(temp_c)
    freqs = np.asarray(freqs, dtype=float)
    k_real = 2.0 * np.pi * freqs / c  # (F,)

    F = len(freqs)
    t11 = np.ones(F, dtype=complex)
    t12 = np.zeros(F, dtype=complex)
    t21 = np.zeros(F, dtype=complex)
    t22 = np.ones(F, dtype=complex)

    for r_seg in r_mid:
        if damping:
            alpha = kirchhoff_alpha(freqs, r_seg, temp_c)
            k = k_real + (1.0 - 1.0j) * alpha
        else:
            k = k_real.astype(complex)

        area = np.pi * r_seg ** 2
        Zc = rho * c / area
        kl = k * seg_len
        cos_kl = np.cos(kl)
        j_sin_kl = 1j * np.sin(kl)

        a11, a12 = cos_kl, Zc * j_sin_kl
        a21, a22 = j_sin_kl / Zc, cos_kl

        n11 = t11 * a11 + t12 * a21
        n12 = t11 * a12 + t12 * a22
        n21 = t21 * a11 + t22 * a21
        n22 = t21 * a12 + t22 * a22
        t11, t12, t21, t22 = n11, n12, n21, n22

    t21 = np.where(np.abs(t21) < 1e-30, 1e-30 + 0j, t21)
    return t22 / t21


# ─────────────────────────────────────────────────────────────
# 3) 입구 방사 임피던스
# ─────────────────────────────────────────────────────────────
def radiation_impedance(freqs, r_mouth, temp_c=config.AIR_TEMP_C, exact=True):
    """
    원형 개구(무한 배플) 방사 임피던스 — 배플 피스톤 '정확해':

        Z = (ρc/S) · [ 1 - J1(2ka)/ka + j·H1(2ka)/ka ]   (J1: 베셀, H1: 스트루브)

    소-ka 근사식 (ka)²/2 + j·0.8216·ka 는 ka ≳ 1 (넓은 입구 × 고주파,
    예: r=30mm에서 1.8kHz 이상)에서 관구보정을 과대평가해 공명 위치를
    틀리게 함 → 정확해가 기본. exact=False는 비교/디버그용.
    ※ torch 포팅(PINN) 시 스트루브 함수는 유리함수 근사로 대체 예정.
    """
    c = config.air_speed_of_sound(temp_c)
    rho = config.air_density(temp_c)
    k = 2.0 * np.pi * np.asarray(freqs, dtype=float) / c
    ka = k * r_mouth
    S = np.pi * r_mouth ** 2
    if exact:
        from scipy.special import j1, struve
        x = 2.0 * ka
        R = 1.0 - 2.0 * j1(x) / np.where(x < 1e-12, 1e-12, x)
        X = 2.0 * struve(1, x) / np.where(x < 1e-12, 1e-12, x)
        return (rho * c / S) * (R + 1j * X)
    return (rho * c / S) * (0.5 * ka ** 2 + 1j * 0.8216 * ka)


# ─────────────────────────────────────────────────────────────
# 4) 관측량: 비율 전달함수 (딥)
# ─────────────────────────────────────────────────────────────
def mic_ratio_response(freqs, z_in, r_mouth,
                       d_mic=config.MIC_HEIGHT,
                       d_spk=config.SPEAKER_DIST,
                       temp_c=config.AIR_TEMP_C):
    """
    관측량 H(f) = p_mic(컵) / p_mic(강체 기준면).  (복소, shape=(F,))

    기준면:  p_ref = e^{-jk(ds-dm)}/(ds-dm) + e^{-jk(ds+dm)}/(ds+dm)
             (직접음 + 이미지 반사)
    컵:      p_cup = p_ref + p_scat
      입구로 빨려드는 유량:  U_in = p_blocked / (Z_in + Z_rad),
                            p_blocked = 2·e^{-jk·ds}/ds
      되쏘는 유량: U_out = -U_in
      마이크 압력(배플 피스톤 축상 '정확해' — 근접장 유효):
        p_scat(d) = (ρc/S)·U_out·[e^{-jk·d} - e^{-jk·√(d²+a²)}]
      ※ 단극(1/2πd) 근사는 d ≲ a 근접장에서 부정확 → 사용 금지.

    스피커 세기·마이크 감도 등 공통 인자는 비율에서 약분 → 진폭 상수 생략.
    """
    c = config.air_speed_of_sound(temp_c)
    rho = config.air_density(temp_c)
    freqs = np.asarray(freqs, dtype=float)
    k = 2.0 * np.pi * freqs / c

    r_direct = d_spk - d_mic
    r_image = d_spk + d_mic
    p_ref = np.exp(-1j * k * r_direct) / r_direct + np.exp(-1j * k * r_image) / r_image

    a = r_mouth
    S = np.pi * a ** 2
    z_rad = radiation_impedance(freqs, a, temp_c)
    p_blocked = 2.0 * np.exp(-1j * k * d_spk) / d_spk
    u_out = -p_blocked / (z_in + z_rad)
    piston_field = np.exp(-1j * k * d_mic) - np.exp(-1j * k * np.sqrt(d_mic ** 2 + a ** 2))
    p_scat = (rho * c / S) * u_out * piston_field

    return (p_ref + p_scat) / p_ref


# ─────────────────────────────────────────────────────────────
# 편의 함수: 프로파일 → 딥 스펙트럼 (한 번에)
# ─────────────────────────────────────────────────────────────
def dip_spectrum(z_grid, r_grid, freqs=None, temp_c=config.AIR_TEMP_C,
                 damping=True, rig_top_extension=False):
    """
    공동 프로파일 → (freqs, |H|의 log10 스펙트럼).
    rig_top_extension=True 시 §3의 상단 고정 세그먼트(r=50mm, h=5mm)를 입구 쪽에 추가.
    """
    if freqs is None:
        freqs = np.linspace(config.FREQ_MIN, config.FREQ_MAX, config.N_FREQ)

    z_grid = np.asarray(z_grid, dtype=float)
    r_grid = np.asarray(r_grid, dtype=float)
    if rig_top_extension:
        z_grid = np.concatenate([z_grid, [z_grid[-1] + 1e-9, z_grid[-1] + config.RIG_TOP_EXT_H]])
        r_grid = np.concatenate([r_grid, [config.RIG_TOP_EXT_R, config.RIG_TOP_EXT_R]])

    seg_len, r_mid = segment_profile(z_grid, r_grid)
    z_in = input_impedance(freqs, seg_len, r_mid, temp_c, damping)
    r_mouth = float(r_grid[-1])
    h = mic_ratio_response(freqs, z_in, r_mouth, temp_c=temp_c)
    return freqs, np.log10(np.abs(h) + 1e-12)
