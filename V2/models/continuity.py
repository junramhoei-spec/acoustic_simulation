"""
연속방정식 잔차 손실 — §8 PINN 손실 ②(∫A dh = Q·t)의 경량 버전.
컨설턴트 조언("로스 하나 더")과 동일한 개념: 미분가능 TMM 순방향층(PINN 손실 ①) 없이도,
모델이 이미 내놓는 r(z) 25슬롯 예측 + H 예측만으로 "형상이 실제 부은 부피와
내적으로 일치하는가"를 강제할 수 있다.

근사(§4 프로토콜 `v2/data/generate.py` 기준):
  마지막으로 기록된 스텝의 물 높이 h_last ≈ H - AIR_STOP(정지 기준, 30mm).
  오차 원인: ΔV=10mL 반올림(작은 슬롯), MAX_STEPS(128) 캡 도달 시 이 근사 자체가
  깨짐 → is_stop_valid로 그런 샘플은 손실에서 제외한다.

head_h가 detach된 구조(v2/models/rnn.py)에서는 이 손실의 H 방향 gradient가
head_h 파라미터에만 흐르고(트렁크는 무사) r 방향 gradient만 트렁크까지 도달 →
기존 시소 방지 설계를 깨지 않으면서 물리 제약만 얹는다.
"""
import math

import torch

try:
    from .. import config
    from ..data.generate import AIR_STOP, MAX_STEPS
except ImportError:
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from v2 import config
    from v2.data.generate import AIR_STOP, MAX_STEPS


def is_stop_valid(n_steps: int) -> float:
    """1.0 = '마지막 스텝 ≈ H - AIR_STOP' 근사가 유효(MAX_STEPS 캡에 안 걸림)."""
    n_pours = n_steps - 1
    return 0.0 if n_pours >= MAX_STEPS else 1.0


def predicted_volume_upto(pred_r_norm, h_phys):
    """정규화 반지름 예측(B,N_SLOTS) → 높이 h_phys(B,)[m]까지 누적 부피[m³].
    라벨 정의(v2/data/shapes.py: slot_labels)와 동일하게 슬롯을 밴드 내 등가반지름
    상수로 보고 적분(부분 밴드는 겹치는 길이만큼만 반영)."""
    r_phys = config.R_MIN + pred_r_norm * (config.R_MAX - config.R_MIN)
    area = math.pi * r_phys ** 2                                       # (B, N_SLOTS)
    band_lo = torch.arange(config.N_SLOTS, device=pred_r_norm.device,
                            dtype=pred_r_norm.dtype) * config.SLOT_PITCH
    band_hi = band_lo + config.SLOT_PITCH
    h = h_phys.unsqueeze(-1).clamp(min=0.0)                             # (B,1)
    overlap = (torch.minimum(h, band_hi) - band_lo).clamp(0.0, config.SLOT_PITCH)
    return (area * overlap).sum(-1)                                     # (B,)


def continuity_loss(pred_r_norm, pred_h_norm, v_last_phys, stop_valid):
    """예측 형상(r) + 예측 높이(H)가 실제 부은 부피(V_last, 측정 입력값)와
    일치하는지 검사. stop_valid=0 샘플(MAX_STEPS 캡)은 배제."""
    H_phys = config.H_MIN + pred_h_norm * (config.H_MAX - config.H_MIN)
    h_target = H_phys - AIR_STOP
    v_pred = predicted_volume_upto(pred_r_norm, h_target)
    resid = (v_pred - v_last_phys) / config.V_NORM * stop_valid
    denom = stop_valid.sum().clamp(min=1.0)
    return (resid ** 2).sum() / denom
