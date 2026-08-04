"""
RNN(BiLSTM) 모델 (§8 사다리 2칸) — docs/RNN_설계_초안_v1.md 구현.
§7 인터페이스 공유: 입력 X(B,S,F) + V(B,S) + step_mask(B,S) → 출력 H(B,) + 슬롯 r(B,25).

베이스라인과의 차이는 "스텝들 사이"뿐:
  StepEncoder·v_emb·step_mix는 baseline 재사용 → 셋 풀링 대신 (Bi)LSTM이 순서대로 읽음.
  성능 차이가 생기면 원인을 "순서 정보" 하나로 귀속시키기 위한 변인 통제.

시소 대응(초안 §2): head_h는 몸통 출력을 detach하여 "읽기 전용" —
  몸통·인코더의 gradient는 반지름 과제가 독점, 높이는 자기 머리만 학습.
  (CNN 단계에서 눈금 동결·기울기 반전(0.84→1.12)의 범인 = 공유 몸통 힘겨루기)

어블레이션 스위치:
  direction : "bi"(기본) / "uni"(순방향) / "rev"(역방향)   — A2
  summary   : "mix"(마지막+평균+최대, 기본) / "last"        — A3
  detach_h  : True(기본) / False                            — A4
"""
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

try:
    from .. import config
    from .baseline import StepEncoder
except ImportError:
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from v2 import config
    from v2.models.baseline import StepEncoder


def _flip_valid(feat, lengths):
    """패딩은 제자리에 두고 유효 스텝 구간만 뒤집는다 (rev 방향용)."""
    out = feat.clone()
    for i, L in enumerate(lengths.tolist()):
        out[i, :L] = feat[i, :L].flip(0)
    return out


class MaskedSeqRNN(nn.Module):
    def __init__(self, n_bins, d=256, n_slots=config.N_SLOTS,
                 direction="bi", num_layers=1, summary="mix", detach_h=True,
                 dropout=0.2):
        super().__init__()
        assert direction in ("bi", "uni", "rev")
        assert summary in ("mix", "last")
        self.n_bins = n_bins
        self.direction = direction
        self.summary = summary
        self.detach_h = detach_h

        # ── 스텝 안을 읽는 눈: 베이스라인 그대로 ──
        self.step_enc = StepEncoder(d)
        self.v_emb = nn.Sequential(nn.Linear(1, 32), nn.ReLU(), nn.Linear(32, 32))
        self.step_mix = nn.Sequential(nn.Linear(d + 32, d), nn.ReLU())

        # ── 스텝 사이를 잇는 기억: (Bi)LSTM ──
        # 방향별 특징 폭을 d로 통일(양방향은 d/2×2) → 방향 어블레이션(A2)의 공정 비교
        bi = direction == "bi"
        hidden = d // 2 if bi else d
        self.lstm = nn.LSTM(d, hidden, num_layers=num_layers,
                            batch_first=True, bidirectional=bi)

        in_dim = 3 * d if summary == "mix" else d
        self.trunk = nn.Sequential(
            nn.Linear(in_dim, 256), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(256, 256), nn.ReLU(),
        )
        self.head_r = nn.Linear(256, n_slots)
        # 높이 머리: 완성된 특징 위의 얕은 회귀자 (detach로 몸통과 절연)
        self.head_h = nn.Sequential(nn.Linear(256, 64), nn.ReLU(), nn.Linear(64, 1))

    def forward(self, X, V, step_mask):
        # X: (B,S,F), V: (B,S), step_mask: (B,S)
        B, S, F = X.shape
        feat = self.step_enc(X.reshape(B * S, F)).reshape(B, S, -1)
        v = self.v_emb(V.unsqueeze(-1))                       # (B,S,32)
        feat = self.step_mix(torch.cat([feat, v], dim=-1))    # (B,S,d)

        lengths = step_mask.sum(1).long().clamp(min=1)
        if self.direction == "rev":
            feat = _flip_valid(feat, lengths)

        packed = pack_padded_sequence(feat, lengths.cpu(),
                                      batch_first=True, enforce_sorted=False)
        out_p, (h_n, _) = self.lstm(packed)
        out, _ = pad_packed_sequence(out_p, batch_first=True, total_length=S)  # (B,S,d)

        # 마지막 유효 스텝 요약: pack이 길이를 알고 있으므로 h_n이 곧 그 값
        if self.direction == "bi":
            h_last = torch.cat([h_n[-2], h_n[-1]], dim=-1)    # (B,d)
        else:
            h_last = h_n[-1]                                  # (B,d)

        if self.summary == "mix":
            m = step_mask.unsqueeze(-1)                       # (B,S,1)
            mean_pool = (out * m).sum(1) / m.sum(1).clamp(min=1e-6)
            max_pool = out.masked_fill(m == 0, -1e9).max(1).values
            z_in = torch.cat([h_last, mean_pool, max_pool], dim=-1)
        else:
            z_in = h_last

        z = self.trunk(z_in)
        z_h = z.detach() if self.detach_h else z
        return self.head_h(z_h).squeeze(-1), self.head_r(z)
