"""
증강 로더 v1 — §6 전처리 + §9 on-the-fly 증강.
코어는 순수 numpy(테스트·이식 용이), PyTorch Dataset은 얇은 래퍼.

증강 순서(물리 순서와 일치):
  스텝 서브샘플링 → 온도(주파수축 리샘플) → d_mic 지터(미세 시프트)
  → [absolute 모드: 시그니처 곱 + 게인 + 기울기] → 가짜 딥(4~7kHz)
  → 배경소음 바닥(선형 파워 합) → 대역 crop → 시퀀스 z-score
모드:
  "ratio"    : 컵있음/컵없음 비율 관측 — 시그니처·게인 거의 약분(잔여만)
  "absolute" : 절대 스펙트럼 — 시그니처 라이브러리 곱(현장 미세조정용)
시그니처/소음: signatures_dir의 .npy(로그10 스케일, 주파수 그리드 동일)를 로드,
없으면 합성(저차 코사인 합) 생성. 실측 채취 후 파일만 넣으면 교체됨.
"""
import glob
import os

import numpy as np

try:
    from .. import config
except ImportError:
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
    from v2 import config

try:
    from torch.utils.data import Dataset as _BaseDataset
except ImportError:
    _BaseDataset = object

FREQS = np.linspace(config.FREQ_MIN, config.FREQ_MAX, config.N_FREQ)


# ─────────────────────────────────────────────────────────────
# 증강 설정
# ─────────────────────────────────────────────────────────────
class AugmentConfig:
    def __init__(self, mode="ratio", crop_hz=config.CROP_DEFAULT,
                 subsample=True, temp_range=(15.0, 30.0),
                 dmic_jitter_hz=2.0, snr_db=(10.0, 40.0),
                 fake_dip_prob=0.3, signatures_dir=None, enabled=True):
        assert mode in ("ratio", "absolute")
        self.mode = mode
        self.crop_hz = crop_hz
        self.subsample = subsample
        self.temp_range = temp_range
        self.dmic_jitter_hz = dmic_jitter_hz
        self.snr_db = snr_db
        self.fake_dip_prob = fake_dip_prob
        self.signatures_dir = signatures_dir
        self.enabled = enabled  # False = 전처리(§6)만 수행(검증용)

    @property
    def n_bins(self):
        return int(np.sum(FREQS <= self.crop_hz))


def load_or_synth_signatures(cfg, rng, n_synth=32):
    """시그니처 라이브러리: 실측 .npy 우선, 없으면 합성."""
    if cfg.signatures_dir:
        files = sorted(glob.glob(os.path.join(cfg.signatures_dir, "*.npy")))
        if files:
            return np.stack([np.load(f) for f in files])
    sigs = []
    for _ in range(n_synth):
        s = np.zeros_like(FREQS)
        for k in range(1, 5):
            s += rng.uniform(0, 0.15) * np.cos(2 * np.pi * k * FREQS / FREQS[-1] + rng.uniform(0, 2 * np.pi))
        sigs.append(s)
    return np.stack(sigs)


# ─────────────────────────────────────────────────────────────
# 샘플 단위 증강 (log10 도메인)
# ─────────────────────────────────────────────────────────────
def augment_sequence(spec, v_cum, cfg, rng, signatures):
    """spec: (S, 700) log10|H|, v_cum: (S,) [m³] → 증강+전처리 후 (S', n_bins), (S',)"""
    S = len(spec)
    spec = spec.astype(np.float32)

    if cfg.enabled and cfg.subsample and S > 3:
        keep_p = rng.uniform(0.3, 1.0)
        keep = rng.random(S) < keep_p
        keep[0] = keep[-1] = True          # 빈 컵·정지 직전 상태는 항상 유지
        if keep.sum() < 3:
            keep[rng.choice(S, 3, replace=False)] = True
        spec, v_cum = spec[keep], v_cum[keep]

    if cfg.enabled:
        # 온도: 공명 f ∝ c → 주파수축 스케일 γ
        T = rng.uniform(*cfg.temp_range)
        gamma = config.air_speed_of_sound(T) / config.air_speed_of_sound(config.AIR_TEMP_C)
        # d_mic 지터: 근접장 이동 민감도(≈1.7Hz/mm)의 미세 시프트
        df = rng.normal(0, cfg.dmic_jitter_hz)
        src = FREQS / gamma - df
        spec = np.stack([np.interp(src, FREQS, row) for row in spec])

        if cfg.mode == "absolute":
            sig = signatures[rng.integers(len(signatures))]
            spec = spec + sig[None, :]                      # 곱 = log 덧셈
            spec += rng.uniform(-0.5, 0.5)                  # 게인
            spec += rng.uniform(-0.2, 0.2) * (FREQS - FREQS.mean())[None, :] / FREQS[-1]
        else:                                               # ratio: 잔여만
            spec += rng.uniform(-0.05, 0.05)
            spec += rng.uniform(-0.03, 0.03) * (FREQS - FREQS.mean())[None, :] / FREQS[-1]

        if rng.random() < cfg.fake_dip_prob:                # 미모델 반경모드 랜덤화
            for _ in range(rng.integers(1, 3)):
                f0 = rng.uniform(4000, config.FREQ_MAX)
                w = rng.uniform(30, 150)
                depth = rng.uniform(0.2, 1.0)
                spec -= depth / (1 + ((FREQS - f0) / w) ** 2)[None, :]

        # 배경소음 바닥: 선형 파워 합 (딥이 노이즈 바닥에서 멈추는 실측 현상 재현)
        snr = rng.uniform(*cfg.snr_db)
        floor = np.median(spec) - snr / 20.0
        noise = floor + 0.2 * rng.standard_normal(spec.shape)
        spec = 0.5 * np.log10(10 ** (2 * spec) + 10 ** (2 * noise))

    # ── §6 전처리 (증강 여부와 무관하게 항상) ──
    spec = spec[:, FREQS <= cfg.crop_hz]                    # crop
    mu, sd = spec.mean(), spec.std() + 1e-8                 # 시퀀스 전체 z-score
    spec = (spec - mu) / sd
    v_norm = v_cum / config.V_NORM                          # 고정 상수 정규화
    return spec, v_norm.astype(np.float32)


def normalize_labels(H, labels):
    h_n = (H - config.H_MIN) / (config.H_MAX - config.H_MIN)
    r_n = (labels - config.R_MIN) / (config.R_MAX - config.R_MIN)
    return np.float32(h_n), r_n.astype(np.float32)


# ─────────────────────────────────────────────────────────────
# 청크 로더 (래그드 CSR)
# ─────────────────────────────────────────────────────────────
class ChunkStore:
    """dataset/v2/*.npz 를 메모리에 로드하고 샘플 단위 접근 제공."""

    def __init__(self, data_dir, max_samples=None):
        files = sorted(glob.glob(os.path.join(data_dir, "*.npz")))
        if not files:
            raise FileNotFoundError(f"npz 없음: {data_dir}")
        sp, vc, ns, H, lab, msk = [], [], [], [], [], []
        total = 0
        for f in files:
            d = np.load(f)
            sp.append(d["spectra_all"]); vc.append(d["v_cum_all"])
            ns.append(d["n_steps"]); H.append(d["H"])
            lab.append(d["labels"]); msk.append(d["label_mask"])
            total += len(d["n_steps"])
            if max_samples and total >= max_samples:
                break

        spectra_np = np.concatenate(sp)
        v_cum_np = np.concatenate(vc)
        n_steps_np = np.concatenate(ns)
        H_np = np.concatenate(H)
        labels_np = np.concatenate(lab)
        label_mask_np = np.concatenate(msk)
        offsets_np = np.concatenate([[0], np.cumsum(n_steps_np)])

        self.use_shared = False
        try:
            import torch
            self.spectra = torch.from_numpy(spectra_np).share_memory_()
            self.v_cum = torch.from_numpy(v_cum_np).share_memory_()
            self.n_steps = torch.from_numpy(n_steps_np).share_memory_()
            self.H = torch.from_numpy(H_np).share_memory_()
            self.labels = torch.from_numpy(labels_np).share_memory_()
            self.label_mask = torch.from_numpy(label_mask_np).share_memory_()
            self.offsets = torch.from_numpy(offsets_np).share_memory_()
            self.use_shared = True
        except Exception:
            self.spectra = spectra_np
            self.v_cum = v_cum_np
            self.n_steps = n_steps_np
            self.H = H_np
            self.labels = labels_np
            self.label_mask = label_mask_np
            self.offsets = offsets_np

        if max_samples:
            self.n = min(max_samples, len(self.n_steps))
        else:
            self.n = len(self.n_steps)

    def __len__(self):
        return self.n

    def get_raw(self, i):
        if self.use_shared:
            a, b = self.offsets[i].item(), self.offsets[i + 1].item()
            return (
                self.spectra[a:b].numpy(),
                self.v_cum[a:b].numpy(),
                self.H[i].item(),
                self.labels[i].numpy(),
                self.label_mask[i].numpy()
            )
        else:
            a, b = self.offsets[i], self.offsets[i + 1]
            return self.spectra[a:b], self.v_cum[a:b], self.H[i], self.labels[i], self.label_mask[i]


def collate_numpy(items, n_bins):
    """가변 길이 → 패딩 + 스텝 마스크. items: [(spec, v, h_n, r_n, l_mask), ...]"""
    B = len(items)
    S = max(len(it[0]) for it in items)
    X = np.zeros((B, S, n_bins), np.float32)
    V = np.zeros((B, S), np.float32)
    step_mask = np.zeros((B, S), np.float32)
    y_h = np.zeros(B, np.float32)
    y_r = np.zeros((B, config.N_SLOTS), np.float32)
    l_mask = np.zeros((B, config.N_SLOTS), np.float32)
    for b, (spec, v, h_n, r_n, lm) in enumerate(items):
        s = len(spec)
        X[b, :s] = spec; V[b, :s] = v; step_mask[b, :s] = 1.0
        y_h[b] = h_n; y_r[b] = r_n; l_mask[b] = lm
    return X, V, step_mask, y_h, y_r, l_mask


class TorchChunkDataset(_BaseDataset):
    def __init__(self, store, cfg, seed=0):
        self.store = store
        self.cfg = cfg
        self.rng = np.random.default_rng(seed)
        self.signatures = load_or_synth_signatures(cfg, self.rng)

    def __len__(self):
        return len(self.store)

    def __getitem__(self, i):
        spec, v, H, lab, lm = self.store.get_raw(i)
        spec, v = augment_sequence(spec, v, self.cfg, self.rng, self.signatures)
        h_n, r_n = normalize_labels(H, lab)
        return spec, v, h_n, r_n, lm


class TorchChunkCollate:
    def __init__(self, n_bins):
        self.n_bins = n_bins

    def __call__(self, batch):
        import torch
        X, V, sm, yh, yr, lm = collate_numpy(batch, self.n_bins)
        return tuple(torch.from_numpy(a) for a in (X, V, sm, yh, yr, lm))


def make_torch_dataset(store, cfg, seed=0):
    """PyTorch Dataset 래퍼 (torch는 지연 임포트)."""
    return TorchChunkDataset(store, cfg, seed), TorchChunkCollate(cfg.n_bins)
