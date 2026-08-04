import os
import sys
import glob
import json
import torch
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Matplotlib Korean Font setup
for font_name in ['Malgun Gothic', 'NanumGothic', 'AppleGothic', 'Gulim', 'Dotum']:
    if any(font_name in f.name for f in fm.fontManager.ttflist):
        plt.rcParams['font.family'] = font_name
        break
plt.rcParams['axes.unicode_minus'] = False

curr_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(curr_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, curr_dir)

from v2 import config
from v2.data import loader as v2loader
from v2.combine import CombinedPredictor

dev = 'cuda' if torch.cuda.is_available() else 'cpu'

ckpts = sorted(glob.glob(os.path.join(parent_dir, 'dataset', 'models_v2', '*.pt')))
if not ckpts:
    ckpts = sorted(glob.glob(os.path.join(curr_dir, 'dataset', 'models_v2', '*.pt')))

h_ckpt = [c for c in ckpts if 'rnn_sline_nodetach_bestH' in c][0]
r_ckpt = [c for c in ckpts if 'rnn_sline_uni.pt' in c][0]

print(f"Loading CombinedPredictor with H={os.path.basename(h_ckpt)} and r={os.path.basename(r_ckpt)}...")
cp = CombinedPredictor(h_ckpt, r_ckpt, device=dev)
if cp.calib is None:
    cp.calib = (1.0, 0.0)

plot_dir = os.path.join(curr_dir, 'measured_plots_v4')
os.makedirs(plot_dir, exist_ok=True)

file_groups = [
    # Group 1: 7월 실측 세션 (10개)
    {
        "group_id": 1,
        "group_title": "1그룹: 7월 실측 세션 (10개 — 유리/고무/3D프린터/텀블러/매스실린더)",
        "files": [
            '08_3D프린터_벌어진컵_100mm_r15_35mm.json',
            '09_유리_벌어진컵_144mm_r25_42mm.json',
            '10_유리_벌어진컵_82mm_r17_27mm.json',
            '11_3D프린터_일자컵_100mm_r25mm.json',
            '12_매스실린더_180mm_r11mm.json',
            '13_고무_벌어진컵_115mm_r22_38mm.json',
            '14_유리_벌어진컵_83mm_r20_40mm.json',
            '15_텀블러_벌어진컵_138mm_r26_40mm.json',
            '16_유리_오므라진컵_90mm_r34mm.json',
            '17_유리_일자컵_152mm_r29mm.json'
        ]
    },
    # Group 2: 8월 4일 오전 사전 세션 (3개)
    {
        "group_id": 2,
        "group_title": "2그룹: 8월 4일 오전 사전 세션 (3개 — 150mm 대형 일자컵/벌어진컵)",
        "files": [
            '18_일자컵_150mm_r40mm.json',
            '19_일자컵_150mm_r50mm.json',
            '20_벌어진컵1_90mm_초초검검파파.json'
        ]
    },
    # Group 3: 8월 4일 오후 정밀 링 컵 세션 (7개)
    {
        "group_id": 3,
        "group_title": "3그룹: 8월 4일 오후 정밀 링 컵 세션 (7개 — 15mm 색상 링 계단 조합)",
        "files": [
            '01_일자형컵_105mm_r40mm.json',
            '02_벌어진컵_120mm_갈갈초초흰흰검검.json',
            '03_벌어진컵_90mm_초초검검파파.json',
            '04_오므라드는컵_90mm_파파검검초초.json',
            '05_오므라드는컵_120mm_파파파검검검초초.json',
            '06_중앙볼록컵_105mm_초흰검파검흰초.json',
            '07_중앙볼록컵_120mm_갈초흰검검흰초갈.json'
        ]
    }
]

def draw_joint_plot(spec_raw, v_raw, lab_gt, mask_gt, H_gt, pred_r, pred_h, true_z_mm, true_r_mm, title, save_path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 4.4))

    # 1. Left Panel: Spectrogram Waterfall
    v_ml = v_raw * 1e6
    freqs = np.linspace(config.FREQ_MIN, config.FREQ_MAX, spec_raw.shape[1])
    spec_db = 20.0 * spec_raw if np.max(spec_raw) <= 5.0 else spec_raw
    im = ax1.pcolormesh(v_ml, freqs, spec_db.T, cmap="viridis", shading="nearest")
    ax1.set_xlabel("Cumulative volume (mL)", fontsize=8.5)
    ax1.set_ylabel("Frequency (Hz)", fontsize=8.5)
    ax1.set_title("Waterfall: |H| (dB)", fontsize=9.5, fontweight='bold')
    cbar = plt.colorbar(im, ax=ax1)
    cbar.set_label("|H| (dB)", fontsize=8)
    cbar.ax.tick_params(labelsize=7.5)
    ax1.tick_params(labelsize=8)


    # 2. Right Panel: Profile Comparison
    def draw_slots(lab, hh, n_valid, color, label_txt, fill_alpha=0.15, line_width=1.5):
        if n_valid <= 0: return
        z_pts, r_pts = [], []
        for i in range(n_valid):
            lo = i * 10.0
            hi = min((i + 1) * 10.0, hh * 1000.0)
            if hi <= lo: break
            r_mm = lab[i] * 1000.0
            ax2.fill_betweenx([lo, hi], -r_mm, r_mm, color=color, alpha=fill_alpha, lw=0)
            z_pts.extend([lo, hi]); r_pts.extend([r_mm, r_mm])
        if len(z_pts) > 0:
            z_arr, r_arr = np.array(z_pts), np.array(r_pts)
            ax2.plot(r_arr, z_arr, color=color, lw=line_width, label=label_txt)
            ax2.plot(-r_arr, z_arr, color=color, lw=line_width)
            ax2.plot([-r_arr[-1], r_arr[-1]], [z_arr[-1], z_arr[-1]], color=color, lw=line_width)
            ax2.plot([-r_arr[0], r_arr[0]], [z_arr[0], z_arr[0]], color=color, lw=line_width)

    if true_z_mm is not None and true_r_mm is not None and len(true_z_mm) > 0:
        z_arr = np.asarray(true_z_mm, float)
        r_arr = np.asarray(true_r_mm, float)
        ax2.fill_betweenx(z_arr, -r_arr, r_arr, color='#1d4ed8', alpha=0.15, lw=0)
        ax2.plot(r_arr, z_arr, color='#1d4ed8', lw=1.5, label='True (GT)')
        ax2.plot(-r_arr, z_arr, color='#1d4ed8', lw=1.5)
        ax2.plot([-r_arr[-1], r_arr[-1]], [z_arr[-1], z_arr[-1]], color='#1d4ed8', lw=1.5)
        ax2.plot([-r_arr[0], r_arr[0]], [z_arr[0], z_arr[0]], color='#1d4ed8', lw=1.5)
        if H_gt is not None:
            ax2.axhline(H_gt * 1000, color='#1d4ed8', ls='--', lw=1)
    elif lab_gt is not None:
        draw_slots(lab_gt, H_gt, int(mask_gt.sum()), '#1d4ed8', 'True (GT)', fill_alpha=0.15)
        ax2.axhline(H_gt * 1000, color='#1d4ed8', ls='--', lw=1)

    if pred_r is not None:
        pred_n_valid = min(max(int(np.ceil(pred_h * 1000 / 10)), 0), config.N_SLOTS)
        draw_slots(pred_r, pred_h, pred_n_valid, '#dc2626', 'Pred (Ensemble)', fill_alpha=0.15)
        ax2.axhline(pred_h * 1000, color='#dc2626', ls='--', lw=1)

    ax2.set_xlim(-60, 60); ax2.set_ylim(-5, 260)
    ax2.set_xlabel("r (mm)", fontsize=8.5); ax2.set_ylabel("z (mm)", fontsize=8.5)
    ax2.legend(fontsize=8, loc='upper right'); ax2.grid(alpha=0.3)
    ax2.set_title("역추정 형상 프로파일", fontsize=9.5, fontweight='bold')
    ax2.tick_params(labelsize=8)

    fig.suptitle(title, fontsize=10, fontweight='bold', y=0.98)
    fig.tight_layout()
    fig.savefig(save_path, dpi=140)
    plt.close(fig)

global_idx = 1
all_results = []
group_results = {}

for g in file_groups:
    gid = g["group_id"]
    group_results[gid] = {
        "title": g["group_title"],
        "items": []
    }
    for fn in g["files"]:
        jf = os.path.join(curr_dir, 'real_measured_json_all', fn)
        with open(jf, encoding='utf-8') as f:
            d = json.load(f)

        spec_raw = np.asarray(d['spectra_log10'], dtype=np.float32)
        v_raw = np.asarray(d['v_cum_m3'], dtype=np.float64)

        dst_freqs = np.linspace(config.FREQ_MIN, config.FREQ_MAX, config.N_FREQ)
        src_freqs = np.linspace(float(d.get('freq_min', config.FREQ_MIN)),
                                float(d.get('freq_max', config.FREQ_MAX)),
                                spec_raw.shape[1])
        if spec_raw.shape[1] != config.N_FREQ or src_freqs[0] != dst_freqs[0] or src_freqs[-1] != dst_freqs[-1]:
            spec_raw = np.stack([np.interp(dst_freqs, src_freqs, row) for row in spec_raw]).astype(np.float32)

        spec, v = v2loader.augment_sequence(
            spec_raw, v_raw, cp.pre_cfg, np.random.default_rng(0), signatures=None
        )
        S = len(spec)
        X = torch.from_numpy(spec).unsqueeze(0).to(dev)
        V = torch.from_numpy(v).unsqueeze(0).to(dev)
        sm = torch.ones(1, S, device=dev)

        with torch.no_grad():
            ph, pr = cp.forward_batch(X, V, sm)

        pred_h = float(ph[0]) * (config.H_MAX - config.H_MIN) + config.H_MIN
        pred_r = pr[0] * (config.R_MAX - config.R_MIN) + config.R_MIN

        H_gt = d.get('true_H_m')
        lab_gt = np.asarray(d['true_r_m']) if 'true_r_m' in d else None
        mask_gt = np.asarray(d['true_mask']) if 'true_mask' in d else None
        tz_mm = d.get('true_profile_z_mm')
        tr_mm = d.get('true_profile_r_mm')

        err_h = abs(pred_h - H_gt) * 1000.0 if H_gt else 0.0
        err_r = float(np.abs((pred_r - lab_gt) * mask_gt).sum() / max(mask_gt.sum(), 1.0)) * 1000.0 if lab_gt is not None else 0.0

        n_valid_m = min(max(int(np.ceil(pred_h * 1000 / 10)), 1), config.N_SLOTS)
        vol_pred = float(np.sum(np.pi * pred_r[:n_valid_m] ** 2 * config.SLOT_PITCH)) * 1e6

        # Flow metrics
        n_steps = len(v_raw)
        v_cum_ml = v_raw * 1e6
        step_vol_ml = d.get('step_volume_mL')
        if step_vol_ml is None and n_steps > 1:
            step_vol_ml = round(float(v_cum_ml[1] - v_cum_ml[0]), 1)
        tot_inj_ml = round(float(v_cum_ml[-1]), 1) if n_steps > 0 else 0.0

        disp_name = d.get('description', os.path.basename(jf))
        save_img = os.path.join(plot_dir, f'cup_v4_{global_idx:02d}.png')
        t_str = f"#{global_idx:02d} {disp_name}\n[1회 주입: {step_vol_ml}mL | 총 주입: {tot_inj_ml}mL | H 오차: {err_h:.1f}mm | r 오차: {err_r:.1f}mm]"
        
        draw_joint_plot(spec_raw, v_raw, lab_gt, mask_gt, H_gt, pred_r, pred_h, tz_mm, tr_mm, t_str, save_img)

        item_data = {
            'global_idx': global_idx,
            'group_id': gid,
            'filename': fn,
            'name': disp_name,
            'gt_h_mm': H_gt * 1000.0 if H_gt else 0.0,
            'pred_h_mm': pred_h * 1000.0,
            'err_h_mm': err_h,
            'err_r_mm': err_r,
            'vol_pred_ml': vol_pred,
            'n_steps': n_steps,
            'step_vol_ml': step_vol_ml,
            'tot_inj_ml': tot_inj_ml,
            'img_path': save_img,
            'tz_mm': tz_mm,
            'tr_mm': tr_mm
        }
        group_results[gid]["items"].append(item_data)
        all_results.append(item_data)
        global_idx += 1

print(f"Evaluated {len(all_results)} cups with Spectrogram + Profile joint plots.")

res_v4_path = os.path.join(plot_dir, 'results_v4.json')
with open(res_v4_path, 'w', encoding='utf-8') as rf:
    json.dump({
        "all": all_results,
        "groups": group_results
    }, rf, ensure_ascii=False, indent=2)

print(f"Saved results_v4.json at {res_v4_path}")
