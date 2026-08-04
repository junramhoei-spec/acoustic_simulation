"""
베이스라인 모델 (§8 사다리 1칸) — 마스크드 셋 인코더 CNN.
§7 인터페이스: 입력 X(B,S,F) + V(B,S) + step_mask(B,S) → 출력 H(B,) + 슬롯 r(B,25).

구조 철학:
  스텝별 스펙트럼을 1D-CNN으로 인코딩 → V_i 임베딩과 결합 → 마스크드 평균+최대 풀링.
  풀링은 순서 무시(set) — RNN(§8 2칸)과의 비교로 "순서 정보의 기여"를 측정하는 기준점.
"""
import torch
import torch.nn as nn

try:
    from .. import config
except ImportError:
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from v2 import config


class StepEncoder(nn.Module):
    """스펙트럼 1개(F bins) → 특징 벡터(d)."""

    def __init__(self, d=256):
        super().__init__()
        # GroupNorm 사용 이유: 배치에 패딩 스텝(0행)이 섞여도 통계가 오염되지 않고
        # (샘플별 정규화), 배치 1 추론에서도 동작이 동일함.
        self.conv = nn.Sequential(
            nn.Conv1d(1, 16, 7, stride=2, padding=3), nn.GroupNorm(4, 16), nn.ReLU(),
            nn.Conv1d(16, 32, 7, stride=2, padding=3), nn.GroupNorm(4, 32), nn.ReLU(),
            nn.Conv1d(32, 64, 5, stride=2, padding=2), nn.GroupNorm(8, 64), nn.ReLU(),
            nn.Conv1d(64, 64, 5, stride=2, padding=2), nn.GroupNorm(8, 64), nn.ReLU(),
            nn.AdaptiveAvgPool1d(8),
        )
        self.fc = nn.Linear(64 * 8, d)

    def forward(self, x):          # x: (N, F)
        h = self.conv(x.unsqueeze(1))          # (N, 64, 8)
        return self.fc(h.flatten(1))           # (N, d)


class MaskedSetBaseline(nn.Module):
    def __init__(self, n_bins, d=256, n_slots=config.N_SLOTS, dropout=0.2):
        super().__init__()
        self.n_bins = n_bins
        self.step_enc = StepEncoder(d)
        self.v_emb = nn.Sequential(nn.Linear(1, 32), nn.ReLU(), nn.Linear(32, 32))
        self.step_mix = nn.Sequential(nn.Linear(d + 32, d), nn.ReLU())
        self.trunk = nn.Sequential(
            nn.Linear(2 * d, 256), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(256, 256), nn.ReLU(),
        )
        self.head_h = nn.Linear(256, 1)
        self.head_r = nn.Linear(256, n_slots)

    def forward(self, X, V, step_mask):
        # X: (B,S,F), V: (B,S), step_mask: (B,S)
        B, S, F = X.shape
        feat = self.step_enc(X.reshape(B * S, F)).reshape(B, S, -1)
        v = self.v_emb(V.unsqueeze(-1))                       # (B,S,32)
        feat = self.step_mix(torch.cat([feat, v], dim=-1))    # (B,S,d)

        m = step_mask.unsqueeze(-1)                           # (B,S,1)
        mean_pool = (feat * m).sum(1) / m.sum(1).clamp(min=1e-6)
        max_pool = feat.masked_fill(m == 0, -1e9).max(1).values
        z = self.trunk(torch.cat([mean_pool, max_pool], dim=-1))
        return self.head_h(z).squeeze(-1), self.head_r(z)


def masked_loss(pred_h, pred_r, y_h, y_r, l_mask, h_weight=3.0):
    """슬롯: 유효 슬롯만 MSE. 높이: 가중 MSE."""
    loss_r = ((pred_r - y_r) ** 2 * l_mask).sum() / l_mask.sum().clamp(min=1.0)
    loss_h = ((pred_h - y_h) ** 2).mean()
    return loss_r + h_weight * loss_h, loss_r.detach(), loss_h.detach()


@torch.no_grad()
def mae_mm(pred_h, pred_r, y_h, y_r, l_mask):
    """물리 단위(mm) MAE — 사람이 읽는 지표."""
    h_mm = (pred_h - y_h).abs().mean().item() * (config.H_MAX - config.H_MIN) * 1000
    r_mm = (((pred_r - y_r).abs() * l_mask).sum() / l_mask.sum().clamp(min=1.0)).item() \
        * (config.R_MAX - config.R_MIN) * 1000
    return h_mm, r_mm
