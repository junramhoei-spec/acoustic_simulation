import os
import sys
import glob
import json
import time
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

plot_dir = os.path.join(curr_dir, 'measured_plots')
os.makedirs(plot_dir, exist_ok=True)

json_files = sorted(glob.glob(os.path.join(curr_dir, 'real_measured_json_all', '*.json')))
print(f"Evaluating {len(json_files)} real measurement files...")

results = []

def draw_profile_plot(lab_gt, mask_gt, H_gt, pred_r, pred_h, title, save_path):
    fig, ax = plt.subplots(figsize=(3.8, 4.8))

    def draw(lab, hh, n_valid, color, label_txt, fill_alpha=0.15, line_width=1.5):
        if n_valid <= 0: return
        z_pts, r_pts = [], []
        for i in range(n_valid):
            lo = i * 10.0
            hi = min((i + 1) * 10.0, hh * 1000.0)
            if hi <= lo: break
            r_mm = lab[i] * 1000.0
            ax.fill_betweenx([lo, hi], -r_mm, r_mm, color=color, alpha=fill_alpha, lw=0)
            z_pts.extend([lo, hi]); r_pts.extend([r_mm, r_mm])
        if len(z_pts) > 0:
            z_arr, r_arr = np.array(z_pts), np.array(r_pts)
            ax.plot(r_arr, z_arr, color=color, lw=line_width, label=label_txt)
            ax.plot(-r_arr, z_arr, color=color, lw=line_width)
            ax.plot([-r_arr[-1], r_arr[-1]], [z_arr[-1], z_arr[-1]], color=color, lw=line_width)
            ax.plot([-r_arr[0], r_arr[0]], [z_arr[0], z_arr[0]], color=color, lw=line_width)

    if lab_gt is not None:
        draw(lab_gt, H_gt, int(mask_gt.sum()), '#1d4ed8', 'True (GT)', fill_alpha=0.15)
        ax.axhline(H_gt * 1000, color='#1d4ed8', ls='--', lw=1)

    if pred_r is not None:
        pred_n_valid = min(max(int(np.ceil(pred_h * 1000 / 10)), 0), config.N_SLOTS)
        draw(pred_r, pred_h, pred_n_valid, '#dc2626', 'Pred (Ensemble)', fill_alpha=0.15)
        ax.axhline(pred_h * 1000, color='#dc2626', ls='--', lw=1)

    ax.set_xlim(-60, 60); ax.set_ylim(-5, 260)
    ax.set_xlabel('r (mm)'); ax.set_ylabel('z (mm)')
    ax.legend(fontsize=8, loc='upper right'); ax.grid(alpha=0.3); ax.set_title(title, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(save_path, dpi=140)
    plt.close(fig)

for idx, jf in enumerate(json_files, 1):
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

    err_h = abs(pred_h - H_gt) * 1000.0 if H_gt else 0.0
    err_r = float(np.abs((pred_r - lab_gt) * mask_gt).sum() / max(mask_gt.sum(), 1.0)) * 1000.0 if lab_gt is not None else 0.0

    n_valid_m = min(max(int(np.ceil(pred_h * 1000 / 10)), 1), config.N_SLOTS)
    vol_pred = float(np.sum(np.pi * pred_r[:n_valid_m] ** 2 * config.SLOT_PITCH)) * 1e6

    disp_name = d.get('description', os.path.basename(jf))
    save_img = os.path.join(plot_dir, f'cup_{idx:02d}.png')
    t_str = f"#{idx} {disp_name}\nH err: {err_h:.1f}mm | r err: {err_r:.1f}mm"
    draw_profile_plot(lab_gt, mask_gt, H_gt, pred_r, pred_h, t_str, save_img)

    results.append({
        'idx': idx,
        'name': disp_name,
        'gt_h_mm': H_gt * 1000.0 if H_gt else 0.0,
        'pred_h_mm': pred_h * 1000.0,
        'err_h_mm': err_h,
        'err_r_mm': err_r,
        'vol_pred_ml': vol_pred,
        'steps': len(v_raw),
        'img_path': save_img
    })

print(f"Successfully evaluated all {len(results)} cups!")
res_path = os.path.join(plot_dir, 'results.json')
with open(res_path, 'w', encoding='utf-8') as rf:
    json.dump(results, rf, ensure_ascii=False, indent=2)
