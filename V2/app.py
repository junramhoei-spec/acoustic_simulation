"""
음향 형상 역추적 v2 — 통합 앱
실행: streamlit run v2/app.py

탭 구성 (모듈이 완성되는 대로 활성화):
  1. 순방향 탐색기  : 형상 → 딥 스펙트럼 + 물채움 워터폴  [활성]
  2. 데이터셋       : 생성/검사                             [예정]
  3. 학습           : 베이스 모델 학습/미세조정              [예정]
  4. 추론           : 실측/시뮬 추정 + 형상 시각화           [예정]

갱신 2026-08-03: 워터폴 축을 관습에 정합 — x=누적 부피(mL), y=주파수(Hz).
  스텝 번호 축 대신 실제 v_cum 좌표(pcolormesh) 사용 → 불규칙 주입(ΔV 가변)도
  물리적으로 올바른 위치에 그려짐. 데이터/모델/체크포인트 규격 변경 없음(표시 전용).
  (물스랩 최신본 기반 병합: 전문가 결합 실측 추정 UI 유지)
"""
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2 import config
from v2.forward import tmm
from v2.data import loader as v2loader, shapes as v2shapes


# ── matplotlib 한글 폰트 설정 ──
_korean_font_set = False
for _fname in ["Malgun Gothic", "NanumGothic", "AppleGothic", "NanumBarunGothic"]:
    if any(_fname in f.name for f in fm.fontManager.ttflist):
        plt.rcParams["font.family"] = _fname
        plt.rcParams["axes.unicode_minus"] = False
        _korean_font_set = True
        break
if not _korean_font_set:
    plt.rcParams["axes.unicode_minus"] = False

st.set_page_config(page_title="음향 형상 역추적 v2", page_icon="🔊", layout="wide")

PRESETS = ["원통", "원뿔대", "호리병", "소주병", "리그 계단(링)", "커스텀"]

import glob as _glob_init

def _find_best_dir(candidates, ext):
    best_dir = candidates[0]
    max_count = -1
    for d in candidates:
        if os.path.exists(d):
            count = len(_glob_init.glob(os.path.join(d, f"*{ext}")))
            if count > max_count:
                max_count = count
                best_dir = d
    return best_dir

DATA_DIR_DEFAULT = _find_best_dir(["../dataset/v2", "dataset/v2", "v2/dataset/v2", "V2/dataset/v2"], ".npz")
MODELS_DIR_DEFAULT = _find_best_dir(["../dataset/models_v2", "dataset/models_v2", "v2/dataset/models_v2", "V2/dataset/models_v2"], ".pt")


class LazyChunkStore:
    """dataset/v2/*.npz 청크 메타데이터를 0.05초 만에 초고속 로드하고,
    스펙트럼 데이터(spectra_all)는 개별 샘플 조회 시에만 지연 로딩하는 쾌속 데이터 로더."""

    def __init__(self, data_dir, max_samples=None):
        self.data_dir = data_dir
        self.files = sorted(_glob_init.glob(os.path.join(data_dir, "*.npz")))
        if not self.files:
            raise FileNotFoundError(f"npz 없음: {data_dir}")

        ns_list, H_list, lab_list, msk_list = [], [], [], []
        self.chunk_offsets = [0]
        total = 0

        for f in self.files:
            d = np.load(f)
            ns = d["n_steps"]
            ns_list.append(ns)
            H_list.append(d["H"])
            lab_list.append(d["labels"])
            msk_list.append(d["label_mask"])
            n_samples = len(ns)
            total += n_samples
            self.chunk_offsets.append(total)
            if max_samples and total >= max_samples:
                break

        self.n_steps = np.concatenate(ns_list)
        self.H = np.concatenate(H_list)
        self.labels = np.concatenate(lab_list)
        self.label_mask = np.concatenate(msk_list)
        self.offsets = np.concatenate([[0], np.cumsum(self.n_steps)])
        self.chunk_offsets = np.array(self.chunk_offsets)
        self._cache = {}

    def __len__(self):
        return len(self.n_steps)

    def get_raw(self, idx):
        chunk_idx = int(np.searchsorted(self.chunk_offsets, idx, side="right") - 1)
        local_idx = idx - int(self.chunk_offsets[chunk_idx])

        if chunk_idx not in self._cache:
            self._cache[chunk_idx] = np.load(self.files[chunk_idx])
        d = self._cache[chunk_idx]

        n_s = int(d["n_steps"][local_idx])
        H_val = float(d["H"][local_idx])
        lab = d["labels"][local_idx]
        msk = d["label_mask"][local_idx]

        row_start = int(d["n_steps"][:local_idx].sum()) if local_idx > 0 else 0
        row_end = row_start + n_s

        spec = d["spectra_all"][row_start:row_end]
        v_cum = d["v_cum_all"][row_start:row_end]
        return spec, v_cum, H_val, lab, msk



# ─────────────────────────────────────────────────────────────
# 형상 정의
# ─────────────────────────────────────────────────────────────
def build_profile(preset, p):
    """프리셋 + 파라미터 → (z_grid, r_grid) [m]"""
    H = p.get("H")  # 소주병/리그 프리셋은 H 미사용
    if preset == "원통":
        return np.array([0, H]), np.array([p["r1"], p["r1"]])
    if preset == "원뿔대":
        return np.array([0, H]), np.array([p["r1"], p["r2"]])
    if preset == "호리병":
        zn = p["neck_z"] * H
        tw = 0.15 * H
        z = np.linspace(0, H, 60)
        r = np.where(z < zn - tw, p["r1"],
             np.where(z > zn + tw, p["r2"],
              p["r1"] + (p["r2"] - p["r1"]) * 0.5 * (1 - np.cos(np.pi * (z - zn + tw) / (2 * tw)))))
        return z, r
    if preset == "소주병":
        return (np.array([0.0, 0.140, 0.170, 0.210]),
                np.array([0.032, 0.032, 0.013, 0.013]))
    if preset == "리그 계단(링)":
        radii = p["rings"]
        z, r = [0.0], [radii[0]]
        for i, rr in enumerate(radii):
            z += [(i + 1) * 0.015 - 1e-9, (i + 1) * 0.015]
            nxt = radii[i + 1] if i + 1 < len(radii) else rr
            r += [rr, nxt]
        return np.array(z[:-1]), np.array(r[:-1])
    # 커스텀: 등간격 제어점 선형 보간
    ctrl = p["ctrl"]
    return np.linspace(0, H, len(ctrl)), np.array(ctrl)


def profile_volume(z, r, upto=None):
    zz = np.linspace(0, z[-1] if upto is None else upto, 400)
    rr = np.interp(zz, z, r)
    trapz_fn = getattr(np, "trapezoid", getattr(np, "trapz", None))
    return trapz_fn(np.pi * rr ** 2, zz)


def plot_shape(z, r, water_h=None):
    fig, ax = plt.subplots(figsize=(3.2, 4.6))
    zz = np.linspace(0, z[-1], 300)
    rr = np.interp(zz, z, r) * 1000
    zmm = zz * 1000
    ax.fill_betweenx(zmm, -rr, rr, color="#dbeafe")
    ax.plot(rr, zmm, "#1d4ed8", lw=2); ax.plot(-rr, zmm, "#1d4ed8", lw=2)
    if water_h is not None and water_h > 0:
        m = zmm <= water_h * 1000
        ax.fill_betweenx(zmm[m], -rr[m], rr[m], color="#38bdf8", alpha=0.8)
    ax.set_xlim(-60, 60); ax.set_ylim(-5, max(260, zmm[-1] * 1.1))
    ax.set_xlabel("r (mm)"); ax.set_ylabel("z (mm)")
    ax.grid(alpha=0.3); ax.set_aspect("equal")
    fig.tight_layout()
    return fig


@st.cache_data(show_spinner=False)
def fill_waterfall(z_tuple, r_tuple, n_steps, fill_frac, temp_c, damping, rig_ext):
    """물채움 시퀀스: 부피 등간격 n_steps → (수위들, 스펙트럼 행렬)"""
    z = np.array(z_tuple); r = np.array(r_tuple)
    H = z[-1]
    zz = np.linspace(0, H, 400)
    rr = np.interp(zz, z, r)
    v_cum = np.concatenate([[0], np.cumsum(0.5 * (np.pi * rr[:-1] ** 2 + np.pi * rr[1:] ** 2) * np.diff(zz))])
    v_targets = np.linspace(0, v_cum[-1] * fill_frac, n_steps)
    heights = np.interp(v_targets, v_cum, zz)
    freqs = np.linspace(config.FREQ_MIN, config.FREQ_MAX, config.N_FREQ)
    spectra = []
    for wh in heights:
        if H - wh < 0.005:
            spectra.append(np.zeros(config.N_FREQ)); continue
        za = zz[zz >= wh] - wh
        ra = np.interp(zz[zz >= wh], z, r)
        if len(za) < 2 or za[-1] < 1e-4:
            spectra.append(np.zeros(config.N_FREQ)); continue
        _, lh = tmm.dip_spectrum(za, ra, freqs, temp_c=temp_c,
                                 damping=damping, rig_top_extension=rig_ext)
        spectra.append(lh)
    return heights, v_targets, freqs, np.array(spectra)


# ─────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────
st.title("🔊 음향 형상 역추적 v2")
st.caption("설계 기준: docs/연구_설계_프레임_v1.md — 관측량 = 컵있음/컵없음 비율 전달함수(딥)")

tab_fwd, tab_data, tab_train, tab_infer = st.tabs(
    ["1️⃣ 순방향 탐색기", "2️⃣ 데이터셋", "3️⃣ 학습", "4️⃣ 추론"])

with st.sidebar:
    st.header("⚙️ 형상 / 조건")
    preset = st.selectbox("형상 프리셋", PRESETS)
    p = {}
    if preset in ("원통", "원뿔대", "호리병", "커스텀"):
        p["H"] = st.slider("높이 H (mm)", 30, 250, 150) / 1000.0
    if preset == "원통":
        p["r1"] = st.slider("반지름 (mm)", 5, 50, 30) / 1000.0
    elif preset == "원뿔대":
        p["r1"] = st.slider("바닥 반지름 (mm)", 5, 50, 40) / 1000.0
        p["r2"] = st.slider("입구 반지름 (mm)", 5, 50, 20) / 1000.0
    elif preset == "호리병":
        p["r1"] = st.slider("몸통 반지름 (mm)", 5, 50, 35) / 1000.0
        p["r2"] = st.slider("목 반지름 (mm)", 5, 50, 12) / 1000.0
        p["neck_z"] = st.slider("목 시작 위치 (H 비율)", 0.4, 0.9, 0.7)
    elif preset == "리그 계단(링)":
        n_rings = st.slider("링 개수", 3, 10, 6)
        ring_opts = [10, 16, 22, 28, 34, 40]
        p["rings"] = [st.select_slider(f"링 {i+1} 반지름 (mm)", ring_opts,
                                       ring_opts[min(i, 5)]) / 1000.0
                      for i in range(n_rings)]
    elif preset == "커스텀":
        n_ctrl = st.slider("제어점 수", 4, 10, 6)
        p["ctrl"] = [st.slider(f"r@{i}/{n_ctrl-1}·H (mm)", 5, 50, 30, key=f"c{i}") / 1000.0
                     for i in range(n_ctrl)]

    st.divider()
    st.header("🌡️ 물리 조건")
    temp_c = st.slider("기온 (°C)", 0, 40, 20)
    damping = st.toggle("Kirchhoff 감쇠", value=True)
    rig_ext = st.toggle("리그 상단 5mm 확장(r=50)", value=(preset == "리그 계단(링)"))
    crop = st.slider("표시/학습 대역 상한 (Hz)", 2000, int(config.FREQ_MAX), int(config.CROP_DEFAULT), 500)

with tab_fwd:
    z, r = build_profile(preset, p)
    vol_ml = profile_volume(z, r) * 1e6

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("높이", f"{z[-1]*1000:.0f} mm")
    c2.metric("입구 반지름", f"{r[-1]*1000:.0f} mm")
    c3.metric("부피", f"{vol_ml:.0f} mL")
    ka_lim = 0.61 * config.air_speed_of_sound(temp_c) / max(r)
    c4.metric("첫 반경모드(1D 한계)", f"{ka_lim:.0f} Hz",
              delta="대역 내 주의" if ka_lim < crop else "대역 밖 OK",
              delta_color="inverse" if ka_lim < crop else "normal")

    col_shape, col_spec = st.columns([1, 2.2])

    freqs = np.linspace(config.FREQ_MIN, config.FREQ_MAX, config.N_FREQ)
    _, logh = tmm.dip_spectrum(z, r, freqs, temp_c=temp_c, damping=damping,
                               rig_top_extension=rig_ext)

    with col_shape:
        st.subheader("형상")
        st.pyplot(plot_shape(z, r), use_container_width=True)

    with col_spec:
        st.subheader("빈 컵 딥 스펙트럼 (비율 전달함수)")
        fig, ax = plt.subplots(figsize=(8, 3.6))
        m = freqs <= crop
        ax.plot(freqs[m], 20 * logh[m], "#1d4ed8", lw=1.3)
        ax.set_xlabel("Frequency (Hz)"); ax.set_ylabel("|H| (dB)")
        ax.grid(alpha=0.3); fig.tight_layout()
        st.pyplot(fig, use_container_width=True)

        from scipy.signal import find_peaks
        idx, _ = find_peaks(-logh[m], prominence=0.05)
        if len(idx):
            st.caption("검출된 딥: " + ",  ".join(f"{freqs[m][i]:.0f} Hz" for i in idx[:8]))

    st.divider()
    st.subheader("💧 물채움 시퀀스 (워터폴)")
    cc1, cc2, cc3 = st.columns(3)
    n_steps = cc1.slider("스텝 수", 5, 40, 20)
    fill_frac = cc2.slider("채움 비율 (부피)", 0.3, 0.98, 0.9)
    step_view = cc3.slider("단일 스텝 보기", 0, n_steps - 1, 0)

    heights, v_targets, wf_freqs, spectra = fill_waterfall(
        tuple(z), tuple(r), n_steps, fill_frac, temp_c, damping, rig_ext)

    col_a, col_b = st.columns([2.2, 1])
    with col_a:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5.6),
                                       gridspec_kw={"height_ratios": [2, 1.2]})
        mm = wf_freqs <= crop
        # x=누적 부피(mL), y=주파수 — pcolormesh라 스텝 간격이 불균일해도 정확한 위치
        im = ax1.pcolormesh(v_targets * 1e6, wf_freqs[mm], (20 * spectra[:, mm]).T,
                            cmap="viridis", shading="nearest")
        ax1.axvline(v_targets[step_view] * 1e6, color="w", ls="--", lw=0.8, alpha=0.8)
        ax1.set_xlabel("Cumulative volume (mL)"); ax1.set_ylabel("Frequency (Hz)")
        ax1.set_title("Waterfall: |H| (dB)")
        plt.colorbar(im, ax=ax1, pad=0.01)
        ax2.plot(wf_freqs[mm], 20 * spectra[step_view][mm], "#0f766e", lw=1.2)
        ax2.set_xlabel("Frequency (Hz)"); ax2.set_ylabel("|H| (dB)")
        ax2.set_title(f"Step {step_view}: 물 {v_targets[step_view]*1e6:.0f} mL, "
                      f"수위 {heights[step_view]*1000:.0f} mm")
        ax2.grid(alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
    with col_b:
        st.pyplot(plot_shape(z, r, water_h=heights[step_view]), use_container_width=True)

# ─────────────────────────────────────────────────────────────
# 탭 2: 데이터셋 검사
# ─────────────────────────────────────────────────────────────
def plot_spec_waterfall(spec_raw, v_raw, title="스펙트로그램 (Waterfall: |H| dB)"):
    fig, ax = plt.subplots(figsize=(3.4, 4.6))
    v_ml = v_raw * 1e6
    freqs = np.linspace(config.FREQ_MIN, config.FREQ_MAX, spec_raw.shape[1])
    spec_db = 20.0 * spec_raw if np.max(spec_raw) <= 5.0 else spec_raw
    im = ax.pcolormesh(v_ml, freqs, spec_db.T, cmap="viridis", shading="nearest")
    ax.set_xlabel("Cumulative volume (mL)", fontsize=8.5)
    ax.set_ylabel("Frequency (Hz)", fontsize=8.5)
    ax.set_title(title, fontsize=9.5, fontweight="bold")
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("|H| (dB)", fontsize=8)
    cbar.ax.tick_params(labelsize=7.5)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    return fig



def plot_slot_profile(labels_m, mask, H, pred=None, pred_H=None, title="", true_z_mm=None, true_r_mm=None):

    """25슬롯 라벨(등가반지름) → 계단 프로파일. pred가 있으면 겹쳐 그림.
    true_z_mm, true_r_mm 이 전달되면 물리 원본 형상을 정확히 실선으로 그림."""
    fig, ax = plt.subplots(figsize=(3.4, 4.6))

    def draw_slots(lab, hh, n_valid, color, label_txt, fill_alpha=0.15, line_width=1.5):
        if n_valid <= 0:
            return
        z_pts, r_pts = [], []
        for i in range(n_valid):
            lo = i * 10.0
            hi = min((i + 1) * 10.0, hh * 1000.0)
            if hi <= lo:
                break
            r_mm = lab[i] * 1000.0
            ax.fill_betweenx([lo, hi], -r_mm, r_mm, color=color, alpha=fill_alpha, lw=0)
            z_pts.extend([lo, hi])
            r_pts.extend([r_mm, r_mm])

        if len(z_pts) > 0:
            z_arr = np.array(z_pts)
            r_arr = np.array(r_pts)
            ax.plot(r_arr, z_arr, color=color, lw=line_width, label=label_txt)
            ax.plot(-r_arr, z_arr, color=color, lw=line_width)
            ax.plot([-r_arr[-1], r_arr[-1]], [z_arr[-1], z_arr[-1]], color=color, lw=line_width)
            ax.plot([-r_arr[0], r_arr[0]], [z_arr[0], z_arr[0]], color=color, lw=line_width)

    if true_z_mm is not None and true_r_mm is not None and len(true_z_mm) > 0:
        z_arr = np.asarray(true_z_mm, float)
        r_arr = np.asarray(true_r_mm, float)
        ax.fill_betweenx(z_arr, -r_arr, r_arr, color="#1d4ed8", alpha=0.15, lw=0)
        ax.plot(r_arr, z_arr, color="#1d4ed8", lw=1.5, label="True (GT)")
        ax.plot(-r_arr, z_arr, color="#1d4ed8", lw=1.5)
        ax.plot([-r_arr[-1], r_arr[-1]], [z_arr[-1], z_arr[-1]], color="#1d4ed8", lw=1.5)
        ax.plot([-r_arr[0], r_arr[0]], [z_arr[0], z_arr[0]], color="#1d4ed8", lw=1.5)
        if H is not None:
            ax.axhline(H * 1000, color="#1d4ed8", ls="--", lw=1)
    elif labels_m is not None:
        draw_slots(labels_m, H, int(mask.sum()), "#1d4ed8", "True", fill_alpha=0.15)
        ax.axhline(H * 1000, color="#1d4ed8", ls="--", lw=1)

    if pred is not None:
        pred_n_valid = min(max(int(np.ceil(pred_H * 1000 / 10)), 0), config.N_SLOTS)
        draw_slots(pred, pred_H, pred_n_valid, "#dc2626", "Pred", fill_alpha=0.15)
        ax.axhline(pred_H * 1000, color="#dc2626", ls="--", lw=1)

    ax.set_xlim(-60, 60); ax.set_ylim(-5, 260)
    ax.set_xlabel("r (mm)"); ax.set_ylabel("z (mm)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3); ax.set_title(title, fontsize=10)
    fig.tight_layout()
    return fig



with tab_data:
    st.subheader("데이터셋 검사 (§4 프로토콜 v1: ΔV=10mL, 공기기둥 30mm 정지)")
    data_dir = st.text_input("데이터 폴더", DATA_DIR_DEFAULT, key="data_dir_inspect")
    st.caption("생성: `python v2/data/generate.py --samples 12500 --worker_id 1..8` (워커 병렬)")
    import glob as _glob
    if not _glob.glob(os.path.join(data_dir, "*.npz")):
        st.warning("npz 청크가 없습니다. 위 명령으로 먼저 생성하세요.")
    else:
        @st.cache_resource(show_spinner="청크 로딩 중...")
        def _load_store(d):
            return LazyChunkStore(d)
        store = _load_store(data_dir)
        c1, c2, c3 = st.columns(3)
        c1.metric("샘플 수", f"{len(store):,}")
        c2.metric("스텝 중앙값", int(np.median(store.n_steps[:len(store)])))
        c3.metric("총 스펙트럼 행", f"{int(store.offsets[len(store)]):,}")

        col_h, col_s = st.columns(2)
        with col_h:
            fig, ax = plt.subplots(figsize=(5, 2.6))
            ax.hist(store.n_steps[:len(store)], bins=50, color="#3b82f6")
            ax.set_xlabel("steps per cup"); ax.grid(alpha=0.3); fig.tight_layout()
            st.pyplot(fig)
        with col_s:
            fig, ax = plt.subplots(figsize=(5, 2.6))
            ax.hist(store.H[:len(store)] * 1000, bins=50, color="#10b981")
            ax.set_xlabel("height H (mm)"); ax.grid(alpha=0.3); fig.tight_layout()
            st.pyplot(fig)

        st.divider()
        idx_view = st.number_input("샘플 인덱스", 0, len(store) - 1, 0)
        spec, v, H_s, lab, lm = store.get_raw(int(idx_view))
        ca, cb = st.columns([1, 2.2])
        with ca:
            st.pyplot(plot_slot_profile(lab, lm, H_s,
                      title=f"#{idx_view}: H={H_s*1000:.0f}mm, {len(v)}steps"))
        with cb:
            fig, ax = plt.subplots(figsize=(8, 4.4))
            f_grid = np.linspace(config.FREQ_MIN, config.FREQ_MAX, spec.shape[1])
            im = ax.pcolormesh(v * 1e6, f_grid, (spec.astype(np.float32) * 20).T,
                               cmap="viridis", shading="nearest")
            ax.set_xlabel("Cumulative volume (mL)"); ax.set_ylabel("Frequency (Hz)")
            plt.colorbar(im, ax=ax, pad=0.01, label="|H| dB")
            fig.tight_layout()
            st.pyplot(fig)

# ─────────────────────────────────────────────────────────────
# 탭 3: 학습
# ─────────────────────────────────────────────────────────────
with tab_train:
    st.subheader("모델 학습 (§8 사다리)")
    try:
        import torch as _torch
        gpus = [f"cuda:{i}" for i in range(_torch.cuda.device_count())]
    except ImportError:
        _torch, gpus = None, []
        st.error("PyTorch가 설치되어 있지 않습니다: `pip install torch`")

    c1, c2 = st.columns(2)
    with c1:
        tr_model = st.radio("모델 (§8 사다리)", ["set", "rnn"], horizontal=True,
                            help="set=CNN 셋 풀링(1칸, 순서 무시) / rnn=BiLSTM(2칸, 순서 기억+H헤드 detach)")
        tr_data = st.text_input("데이터 폴더", DATA_DIR_DEFAULT, key="tr_data")
        tr_mode = st.radio("증강 모드", ["ratio", "absolute"], horizontal=True,
                           help="ratio=비율 관측(안전망) / absolute=시그니처 곱(현장 미세조정 계열)")
        tr_crop = st.select_slider("학습 대역 crop (Hz)", [4000, 5000, 7000], 5000)
        tr_name = st.text_input("모델 이름", f"{'rnn' if tr_model == 'rnn' else 'base'}_{tr_mode}")
    with c2:
        tr_epochs = st.number_input("Epochs", 1, 200, 30)
        tr_batch = st.number_input("Batch", 8, 512, 64)
        tr_lr = st.number_input("Learning rate", value=1e-3, format="%.4f")
        tr_samples = st.number_input("샘플 수 제한 (0=전체)", 0, 500000, 0)
        tr_device = st.selectbox("장치", (gpus + ["cpu"]) if gpus else ["cpu"])

    if st.button("🚀 학습 시작", type="primary", disabled=_torch is None):
        from v2.train import train as v2train
        pbar = st.progress(0.0)
        status = st.empty()
        chart_ph = st.empty()

        def cb(ep, total, msg, history):
            pbar.progress(ep / total)
            status.text(msg)
            h = np.array([row[:3] for row in history])   # (ep, train, val) — 성분 열 개수와 무관
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.plot(h[:, 0], h[:, 1], label="train"); ax.plot(h[:, 0], h[:, 2], label="val")
            if len(history[0]) >= 7:                     # 성분 로그 있으면 시소 판정용 표시
                comp = np.array([(row[0], row[5], row[6]) for row in history])
                ax.plot(comp[:, 0], comp[:, 1], "--", alpha=0.6, label="val r")
                ax.plot(comp[:, 0], comp[:, 2], "--", alpha=0.6, label="val h")
            ax.set_yscale("log"); ax.set_xlabel("epoch"); ax.legend(); ax.grid(alpha=0.3)
            fig.tight_layout(); chart_ph.pyplot(fig); plt.close(fig)

        with st.spinner("데이터셋 청크 로드 및 훈련 준비 중 (수 분 소요될 수 있음)..."):
            ckpt, hist = v2train(tr_data, tr_mode, float(tr_crop), int(tr_epochs),
                                 int(tr_batch), float(tr_lr),
                                 None if tr_samples == 0 else int(tr_samples),
                                 tr_device, tr_name, progress_cb=cb,
                                 model_type=tr_model)
        st.success(f"학습 완료 — 저장: {ckpt}")

# ─────────────────────────────────────────────────────────────
# 탭 4: 추론
# ─────────────────────────────────────────────────────────────
with tab_infer:
    st.subheader("🔮 형상 추정 및 역추적")
    import glob as _glob2
    ckpts = sorted(_glob2.glob(os.path.join(MODELS_DIR_DEFAULT, "*.pt")))
    if not ckpts:
        st.warning("학습된 모델이 없습니다. 3번 탭에서 먼저 학습하세요.")
    else:
        # ── 추론 방식 선택: 전문가 결합(기본 권장) vs 단일 모델 ──
        infer_mode = st.radio(
            "추론 방식 선택",
            ["전문가 결합 (H 전문가 + r 전문가, 권장)",
             "단일 모델 (지정한 1개 모델 사용)"],
            horizontal=True, key="global_infer_mode"
        )
        use_combined = infer_mode.startswith("전문가 결합")

        def _default_ckpt_idx(paths, keyword):
            for _i, _p in enumerate(paths):
                if keyword in os.path.basename(_p):
                    return _i
            return 0

        h_sel, r_sel, sel = None, None, None
        if use_combined:
            col_h, col_r = st.columns(2)
            with col_h:
                h_sel = st.selectbox(
                    "H 전문가 (높이 담당)", ckpts,
                    index=_default_ckpt_idx(ckpts, "rnn_sline_nodetach_bestH"),
                    format_func=os.path.basename, key="global_h_ckpt")
            with col_r:
                r_sel = st.selectbox(
                    "r 전문가 (반지름 담당)", ckpts,
                    index=_default_ckpt_idx(ckpts, "rnn_sline_uni.pt"),
                    format_func=os.path.basename, key="global_r_ckpt")
            st.caption("💡 확정 권장 조합: "
                       "H=rnn_sline_nodetach_bestH.pt + r=rnn_sline_uni.pt")
        else:
            sel = st.selectbox("단일 모델 선택", ckpts,
                               index=_default_ckpt_idx(ckpts, "rnn_sline_uni.pt"),
                               format_func=os.path.basename, key="global_single_ckpt")

        # ── 범용 추론 헬퍼 ──
        def _predict_shape_seq(spec_seq, v_seq, dev="cpu"):
            """(spec_seq, v_seq) -> (pred_h[m], pred_r[m], info_str)"""
            import torch
            if use_combined:
                from v2.combine import CombinedPredictor
                cp = CombinedPredictor(h_sel, r_sel, device=dev)
                if cp.calib is None:
                    cp.calib = (1.0, 0.0)
                spec, v = v2loader.augment_sequence(
                    np.asarray(spec_seq, np.float32),
                    np.asarray(v_seq, np.float64),
                    cp.pre_cfg, np.random.default_rng(0), signatures=None
                )
                S = len(spec)
                X = torch.from_numpy(spec).unsqueeze(0)
                V = torch.from_numpy(v).unsqueeze(0)
                sm = torch.ones(1, S)
                ph, pr = cp.forward_batch(X, V, sm)
                pred_h = float(ph[0]) * (config.H_MAX - config.H_MIN) + config.H_MIN
                pred_r = pr[0] * (config.R_MAX - config.R_MIN) + config.R_MIN
                info = f"전문가 결합 (H={os.path.basename(h_sel)} + r={os.path.basename(r_sel)})"
            else:
                ck = torch.load(sel, map_location=dev, weights_only=False)
                aug = v2loader.AugmentConfig(mode=ck["aug"]["mode"], crop_hz=ck["aug"]["crop_hz"], enabled=False)
                arch = ck["arch"]
                if arch.get("model") == "rnn":
                    from v2.models.rnn import MaskedSeqRNN
                    model = MaskedSeqRNN(arch["n_bins"], **(arch.get("model_kw") or {})).to(dev)
                else:
                    from v2.models.baseline import MaskedSetBaseline
                    model = MaskedSetBaseline(arch["n_bins"]).to(dev)
                model.load_state_dict(ck["model_state"])
                model.eval()

                rng_m = np.random.default_rng(0)
                x_m, vn_m = v2loader.augment_sequence(
                    np.asarray(spec_seq, np.float32),
                    np.asarray(v_seq, np.float64),
                    aug, rng_m, None
                )
                dummy_r = np.zeros(config.N_SLOTS, np.float32)
                dummy_m = np.ones(config.N_SLOTS, np.float32)
                items = [(x_m, vn_m, np.float32(0.0), dummy_r, dummy_m)]
                X, V, sm, yh, yr, lmk = v2loader.collate_numpy(items, aug.n_bins)
                with torch.no_grad():
                    ph, pr = model(torch.from_numpy(X).to(dev),
                                   torch.from_numpy(V).to(dev),
                                   torch.from_numpy(sm).to(dev))
                cal = ck.get("calib_h")
                ph_n = float(ph.cpu())
                if cal:
                    ph_n = cal["a"] * ph_n + cal["b"]
                pred_h = ph_n * (config.H_MAX - config.H_MIN) + config.H_MIN
                pred_r = pr.cpu().numpy()[0] * (config.R_MAX - config.R_MIN) + config.R_MIN
                info = f"단일 모델 ({os.path.basename(sel)})"

            return pred_h, pred_r, info

        # ── 1. 무작위 테스트 추정 ──
        st.divider()
        st.subheader("🎲 무작위 시뮬레이션 테스트셋 추정")
        n_show = st.slider("표시 샘플 수", 1, 6, 3)

        @st.cache_resource(show_spinner="테스트 데이터 로딩 중...")
        def _load_test_store(data_dir, max_samples):
            return LazyChunkStore(data_dir, max_samples=max_samples)

        if st.button("🎲 무작위 테스트 추정 실행"):
            import torch
            dev = "cuda" if torch.cuda.is_available() else "cpu"
            split = {}
            if use_combined:
                ck_r = torch.load(r_sel, map_location=dev, weights_only=False)
                ck_h = torch.load(h_sel, map_location=dev, weights_only=False)
                split = ck_r.get("split") or ck_h.get("split") or {}
            else:
                ck_single = torch.load(sel, map_location=dev, weights_only=False)
                split = ck_single.get("split") or {}

            raw_data_dir = split.get("data_dir", DATA_DIR_DEFAULT)
            data_dir = raw_data_dir if os.path.exists(raw_data_dir) else DATA_DIR_DEFAULT
            max_samples = split.get("max_samples", None)

            store2 = _load_test_store(data_dir, max_samples)
            if "test_idx" in split and split["test_idx"]:
                test_idx = [i for i in split["test_idx"] if i < len(store2)]
            else:
                n_total = len(store2)
                rng_split = np.random.default_rng(42)
                perm = rng_split.permutation(n_total)
                test_idx = perm[int(n_total * 0.8):].tolist()

            rng = np.random.default_rng()
            picks = rng.choice(test_idx, min(n_show, len(test_idx)), replace=False)

            for i in picks:
                spec_raw, v_raw, H_s, lab, lm = store2.get_raw(int(i))
                pred_h, pred_r, info = _predict_shape_seq(spec_raw, v_raw, dev=dev)

                err_h = abs(pred_h - H_s) * 1000
                err_r = float(np.abs((pred_r - lab) * lm).sum() / lm.sum()) * 1000

                col_shape, col_spec = st.columns([1.2, 2.2])
                with col_shape:
                    st.pyplot(plot_slot_profile(lab, lm, H_s, pred_r, pred_h,
                              title=f"#{i}  H err {err_h:.1f}mm / r err {err_r:.1f}mm"))
                    st.caption(f"⚙️ {info}")
                with col_spec:
                    fig, ax = plt.subplots(figsize=(6, 4.4))
                    f_grid = np.linspace(config.FREQ_MIN, config.FREQ_MAX, spec_raw.shape[1])
                    im = ax.pcolormesh(v_raw * 1e6, f_grid, (spec_raw * 20).T,
                                       cmap="viridis", shading="nearest")
                    ax.set_xlabel("Cumulative volume (mL)"); ax.set_ylabel("Frequency (Hz)")
                    ax.set_title(f"#{i}: H={H_s*1000:.0f}mm, {len(v_raw)} steps")
                    plt.colorbar(im, ax=ax, pad=0.01, label="|H| dB")
                    fig.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)
                st.divider()

        # ── 2. 현재 사이드바 형상 실시간 추정 ──
        st.divider()
        st.subheader("🔮 현재 사이드바에 정의된 형상 실시간 추정")
        st.caption("사이드바에서 설정한 컵 형상(예: 리그 계단, 소주병, 커스텀 등)에 대해 물채움 시퀀스를 생성한 후 선택한 추론 방식으로 실시간 추정을 진행합니다.")
        if st.button("🔮 현재 사이드바 형상 추정 실행"):
            import torch
            dev = "cuda" if torch.cuda.is_available() else "cpu"

            z_sb, r_sb = build_profile(preset, p)
            H_sb = float(z_sb[-1])
            zz_sb, V_sb = v2shapes.volume_profile(z_sb, r_sb)

            DELTA_V_VAL = 10e-6
            AIR_STOP_VAL = 0.030
            v_stop = float(np.interp(max(H_sb - AIR_STOP_VAL, 0.0), zz_sb, V_sb))
            n_pours = min(int(v_stop / DELTA_V_VAL), 128)

            if n_pours < 4:
                st.error("형상 부피가 너무 작거나 높이가 낮아 추정이 불가능합니다 (최소 4스텝의 물 채우기가 필요합니다).")
            else:
                v_cum = np.arange(n_pours + 1) * DELTA_V_VAL
                heights_sb = np.interp(v_cum, V_sb, zz_sb)

                freqs_eval = np.linspace(config.FREQ_MIN, config.FREQ_MAX, config.N_FREQ)
                spectra_eval = np.empty((n_pours + 1, len(freqs_eval)), dtype=np.float32)
                for idx_sb, wh in enumerate(heights_sb):
                    m = zz_sb >= wh
                    za = zz_sb[m] - wh
                    ra = np.interp(zz_sb[m], z_sb, r_sb)
                    _, lh = tmm.dip_spectrum(za, ra, freqs_eval, temp_c=temp_c, damping=damping, rig_top_extension=rig_ext)
                    spectra_eval[idx_sb] = lh

                labels_sb, mask_sb = v2shapes.slot_labels(z_sb, r_sb)

                pred_h, pred_r, info = _predict_shape_seq(spectra_eval, v_cum, dev=dev)

                err_h = abs(pred_h - H_sb) * 1000
                err_r = float(np.abs((pred_r - labels_sb) * mask_sb).sum() / mask_sb.sum()) * 1000

                col_res1, col_res2 = st.columns([1.2, 2.2])
                with col_res1:
                    st.pyplot(plot_slot_profile(labels_sb, mask_sb, H_sb, pred_r, pred_h,
                              title=f"실시간 추정: H 오차 {err_h:.1f}mm / r 오차 {err_r:.1f}mm"))
                    st.caption(f"⚙️ {info}")
                with col_res2:
                    fig, ax = plt.subplots(figsize=(6, 4.4))
                    im = ax.pcolormesh(v_cum * 1e6, freqs_eval, (spectra_eval * 20).T,
                                       cmap="viridis", shading="nearest")
                    ax.set_xlabel("Cumulative volume (mL)"); ax.set_ylabel("Frequency (Hz)")
                    plt.colorbar(im, ax=ax, pad=0.01, label="|H| dB")
                    fig.tight_layout()
                    st.pyplot(fig)

        # ── 3. 실측 데이터 추정 (단일 / 다중 / 20개 전체 일괄 추정) ──────
        st.divider()
        st.subheader("📥 실측 데이터 추정 (단일 / 다중 / 20개 전체 일괄 추정)")
        st.caption("measurement_tool.html 내보내기 JSON 또는 `v2/real_measured_json_all` 저장 폴더의 20개 실측 파일들을 한 번에 일괄 추정합니다.")

        real_all_dir = _find_best_dir(["v2/real_measured_json_all", "real_measured_json_all", "../v2/real_measured_json_all"], ".json")
        saved_jsons = sorted(_glob_init.glob(os.path.join(real_all_dir, "*.json")))

        c_btn, c_info = st.columns([1.5, 2.5])
        with c_btn:
            run_batch_all = st.button("📁 저장된 실측 20개 파일 한 번에 일괄 추정", type="primary", use_container_width=True)
        with c_info:
            if saved_jsons:
                st.caption(f"💡 `real_measured_json_all` 폴더에 총 {len(saved_jsons)}개의 원본 형상이 포함된 실측 JSON이 준비되어 있습니다.")

        ups = st.file_uploader("실측 스펙트럼 JSON 파일 선택/업로드 (여러 개 동시 선택 가능)", type=["json"],
                               accept_multiple_files=True, key="meas_json_multi")

        items_to_process = []
        import json as _json
        if run_batch_all and saved_jsons:
            for s_fp in saved_jsons:
                try:
                    with open(s_fp, encoding="utf-8") as f:
                        items_to_process.append((os.path.basename(s_fp), _json.load(f)))
                except Exception as ex:
                    st.error(f"{s_fp} 로드 실패: {ex}")
        elif ups:
            for up_f in ups:
                try:
                    items_to_process.append((up_f.name, _json.load(up_f)))
                except Exception as ex:
                    st.error(f"{up_f.name} JSON 파싱 실패: {ex}")

        if items_to_process:
            import torch
            import pandas as pd
            dev = "cuda" if torch.cuda.is_available() else "cpu"
            st.success(f"총 {len(items_to_process)}개 실측 세션 추정 진행 중...")

            summary_rows = []
            plot_items = []

            for item_name, meas in items_to_process:
                if meas.get("type") != "v2_infer_spectra":
                    st.warning(f"[{item_name}] 알 수 없는 type: {meas.get('type')!r} — 스킵합니다.")
                    continue
                spec_m = np.asarray(meas["spectra_log10"], dtype=np.float32)
                v_m = np.asarray(meas["v_cum_m3"], dtype=np.float32)

                dst_freqs = np.linspace(config.FREQ_MIN, config.FREQ_MAX, config.N_FREQ)
                src_freqs = np.linspace(float(meas.get("freq_min", config.FREQ_MIN)),
                                        float(meas.get("freq_max", config.FREQ_MAX)),
                                        spec_m.shape[1])
                if spec_m.shape[1] != config.N_FREQ or src_freqs[0] != dst_freqs[0] or src_freqs[-1] != dst_freqs[-1]:
                    spec_m = np.stack([np.interp(dst_freqs, src_freqs, row) for row in spec_m]).astype(np.float32)

                try:
                    pred_h, pred_r, info = _predict_shape_seq(spec_m, v_m, dev=dev)
                except Exception as ex:
                    st.error(f"[{item_name}] 추론 실패: {ex}")
                    continue

                labels_gt = np.asarray(meas["true_r_m"], dtype=np.float32) if "true_r_m" in meas else None
                mask_gt = np.asarray(meas["true_mask"], dtype=np.float32) if "true_mask" in meas else None
                H_gt = float(meas["true_H_m"]) if "true_H_m" in meas else None

                err_h_mm, err_r_mm = None, None
                if labels_gt is not None and H_gt is not None:
                    if mask_gt is None:
                        mask_gt = (labels_gt > 0).astype(np.float32)
                    err_h_mm = abs(pred_h - H_gt) * 1000.0
                    err_r_mm = float(np.abs((pred_r - labels_gt) * mask_gt).sum() / max(mask_gt.sum(), 1.0)) * 1000.0

                n_valid_m = min(max(int(np.ceil(pred_h * 1000 / 10)), 1), config.N_SLOTS)
                vol_pred = float(np.sum(np.pi * pred_r[:n_valid_m] ** 2 * config.SLOT_PITCH)) * 1e6

                n_steps = len(v_m)
                v_cum_ml = v_m * 1e6
                step_vol_ml = meas.get('step_volume_mL')
                if step_vol_ml is None and n_steps > 1:
                    step_vol_ml = round(float(v_cum_ml[1] - v_cum_ml[0]), 1)
                tot_inj_ml = round(float(v_cum_ml[-1]), 1) if n_steps > 0 else 0.0

                disp_name = meas.get("description", item_name)
                summary_rows.append({
                    "실측 대상 컵": disp_name,
                    "1회 주입 (mL)": f"{step_vol_ml} mL" if step_vol_ml else "-",
                    "총 주입 (mL)": f"{tot_inj_ml:.1f} mL",
                    "스텝 수": f"{n_steps} s",
                    "참값 H (mm)": f"{H_gt*1000:.1f}" if H_gt else "-",
                    "예측 H (mm)": f"{pred_h*1000:.1f}",
                    "H 오차 (mm)": f"{err_h_mm:.1f}" if err_h_mm is not None else "-",
                    "r 오차 (mm)": f"{err_r_mm:.1f}" if err_r_mm is not None else "-",
                    "예측 부피 (mL)": f"{vol_pred:.0f}"
                })

                tz_mm = meas.get("true_profile_z_mm")
                tr_mm = meas.get("true_profile_r_mm")
                plot_items.append({
                    "name": disp_name,
                    "labels_gt": labels_gt,
                    "mask_gt": mask_gt,
                    "H_gt": H_gt,
                    "pred_r": pred_r,
                    "pred_h": pred_h,
                    "err_h_mm": err_h_mm,
                    "err_r_mm": err_r_mm,
                    "spec_m": spec_m,
                    "v_m": v_m,
                    "tz_mm": tz_mm,
                    "tr_mm": tr_mm,
                    "step_vol_ml": step_vol_ml,
                    "tot_inj_ml": tot_inj_ml,
                    "n_steps": n_steps,
                    "vol_pred": vol_pred
                })

            # 1. 요약 메트릭
            valid_h_errs = [float(r["H 오차 (mm)"]) for r in summary_rows if r["H 오차 (mm)"] != "-"]
            valid_r_errs = [float(r["r 오차 (mm)"]) for r in summary_rows if r["r 오차 (mm)"] != "-"]

            if valid_h_errs and valid_r_errs:
                m_c1, m_c2, m_c3 = st.columns(3)
                m_c1.metric("전체 평균 H 높이 오차", f"{np.mean(valid_h_errs):.2f} mm")
                m_c2.metric("전체 평균 r 반지름 오차", f"{np.mean(valid_r_errs):.2f} mm")
                m_c3.metric("평가 완료 세션", f"{len(valid_h_errs)} / {len(summary_rows)} 개")

            # 2. 요약 표
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

            # 3. 개별 세션별 스펙트로그램 & 형상 역추적 프로파일 상세
            st.subheader(f"🖼️ 시간 순 실측 세션 상세 분석 ({len(plot_items)}개)")
            for idx_p, item in enumerate(plot_items, 1):
                p_name = item["name"]
                eh, er = item["err_h_mm"], item["err_r_mm"]
                with st.expander(f"#{idx_p:02d}. {p_name} (H오차: {eh:.1f}mm | r오차: {er:.1f}mm)", expanded=(idx_p <= 3)):
                    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                    c_m1.metric("1회 주입 유량", f"{item['step_vol_ml']} mL")
                    c_m2.metric("실제 총 주입 유량", f"{item['tot_inj_ml']:.1f} mL")
                    c_m3.metric("측정 스텝 수", f"{item['n_steps']} 스텝")
                    c_m4.metric("예측 컵 부피", f"{item['vol_pred']:.0f} mL")

                    c_spec, c_prof = st.columns(2)
                    with c_spec:
                        st.pyplot(plot_spec_waterfall(item["spec_m"], item["v_m"], title="음향 공명 스펙트로그램"))
                    with c_prof:
                        t_str = f"#{idx_p:02d} 형상 프로파일 비교\nH err {eh:.1f}mm / r err {er:.1f}mm"
                        st.pyplot(plot_slot_profile(
                            item["labels_gt"], item["mask_gt"], item["H_gt"],
                            item["pred_r"], item["pred_h"],
                            title=t_str, true_z_mm=item["tz_mm"], true_r_mm=item["tr_mm"]
                        ))



