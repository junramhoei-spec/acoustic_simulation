import os
import sys
import glob
import json
import numpy as np

sys.path.insert(0, os.getcwd())
from v2 import config

out_dir = r"v2\real_measured_json_all"
os.makedirs(out_dir, exist_ok=True)

COLOR_R = {
    '파': 0.040,  # 4cm = 40mm
    '검': 0.034,  # 3.4cm = 34mm
    '흰': 0.028,  # 2.8cm = 28mm
    '초': 0.022,  # 2.2cm = 22mm
    '갈': 0.010,  # 1cm = 10mm
}

def make_ring_profile_exact(colors):
    z_b = np.array([i * 0.015 for i in range(len(colors) + 1)])
    r_v = np.array([COLOR_R[c] for c in colors])
    
    # Exact step profile points for plotting (z_plot, r_plot)
    z_plot = [0.0]
    r_plot = [r_v[0]]
    for i, rv in enumerate(r_v):
        z_end = (i + 1) * 0.015
        z_plot.append(z_end - 1e-6)
        r_plot.append(rv)
        if i + 1 < len(r_v):
            z_plot.append(z_end)
            r_plot.append(r_v[i + 1])
            
    return z_b, r_v, np.array(z_plot), np.array(r_plot)

def slot_labels_piecewise(z_b, r_v, n_slots=25, slot_pitch=0.010):
    H = z_b[-1]
    labels = np.zeros(n_slots, dtype=np.float32)
    mask = np.zeros(n_slots, dtype=np.float32)
    for i in range(n_slots):
        lo, hi = i * slot_pitch, (i + 1) * slot_pitch
        if lo >= H:
            break
        hi_c = min(hi, H)
        zz = np.linspace(lo, hi_c - 1e-9, 200)
        idx = np.searchsorted(z_b, zz, side='right') - 1
        idx = np.clip(idx, 0, len(r_v) - 1)
        rr = r_v[idx]
        A_mean = np.mean(np.pi * rr ** 2)
        labels[i] = np.sqrt(A_mean / np.pi)
        mask[i] = 1.0
    return labels, mask

def slot_labels_continuous(z_pts, r_pts, n_slots=25, slot_pitch=0.010):
    H = z_pts[-1]
    labels = np.zeros(n_slots, dtype=np.float32)
    mask = np.zeros(n_slots, dtype=np.float32)
    for i in range(n_slots):
        lo, hi = i * slot_pitch, (i + 1) * slot_pitch
        if lo >= H:
            break
        hi_c = min(hi, H)
        zz = np.linspace(lo, hi_c, 200)
        rr = np.interp(zz, z_pts, r_pts)
        A_mean = np.mean(np.pi * rr ** 2)
        labels[i] = np.sqrt(A_mean / np.pi)
        mask[i] = 1.0
    return labels, mask

ring_datasets = [
    {
        'src': r'v2\output_실측 물채움\1. 일자형 컵 (높이 105mm 7개, 반지름 4cm)',
        'out_name': '01_일자형컵_105mm_r40mm.json',
        'desc': '1. 일자형 컵 (높이 105mm, 파란색 링 7개, 반지름 4cm)',
        'colors': ['파','파','파','파','파','파','파']
    },
    {
        'src': r'v2\output_실측 물채움\2. 벌어진 컵 (높이 120mm, 8개이므로 갈갈초초흰흰검검)',
        'out_name': '02_벌어진컵_120mm_갈갈초초흰흰검검.json',
        'desc': '2. 벌어진 컵 (높이 120mm, 8개: 갈갈초초흰흰검검)',
        'colors': ['갈','갈','초','초','흰','흰','검','검']
    },
    {
        'src': r'v2\output_실측 물채움\3. 벌어진 컵 (높이 90mm, 6개이므로 초초검검파파)',
        'out_name': '03_벌어진컵_90mm_초초검검파파.json',
        'desc': '3. 벌어진 컵 (높이 90mm, 6개: 초초검검파파)',
        'colors': ['초','초','검','검','파','파']
    },
    {
        'src': r'v2\output_실측 물채움\4. 오므라드는 컵(높이 90mm, 파파검검초초)',
        'out_name': '04_오므라드는컵_90mm_파파검검초초.json',
        'desc': '4. 오므라드는 컵 (높이 90mm, 6개: 파파검검초초)',
        'colors': ['파','파','검','검','초','초']
    },
    {
        'src': r'v2\output_실측 물채움\5. 오므라드는 컵(높이 120mm, 파파파검검검초초)',
        'out_name': '05_오므라드는컵_120mm_파파파검검검초초.json',
        'desc': '5. 오므라드는 컵 (높이 120mm, 8개: 파파파검검검초초)',
        'colors': ['파','파','파','검','검','검','초','초']
    },
    {
        'src': r'v2\output_실측 물채움\6. 중앙이 볼록한 컵 (높이 105mm, 초흰검파검흰초)',
        'out_name': '06_중앙볼록컵_105mm_초흰검파검흰초.json',
        'desc': '6. 중앙이 볼록한 컵 (높이 105mm, 7개: 초흰검파검흰초)',
        'colors': ['초','흰','검','파','검','흰','초']
    },
    {
        'src': r'v2\output_실측 물채움\7. 중앙이 볼록한 컵 (높이 120mm, 갈초흰검검흰초갈)',
        'out_name': '07_중앙볼록컵_120mm_갈초흰검검흰초갈.json',
        'desc': '7. 중앙이 볼록한 컵 (높이 120mm, 8개: 갈초흰검검흰초갈)',
        'colors': ['갈','초','흰','검','검','흰','초','갈']
    },
    {
        'src': r'v2\output_실측 물채움\2026=08-04 벌어진컵1',
        'out_name': '20_벌어진컵1_90mm_초초검검파파.json',
        'desc': '2026-08-04 벌어진 컵 1 (높이 90mm, 6개: 초초검검파파)',
        'colors': ['초','초','검','검','파','파']
    }
]

continuous_datasets = [
    {
        'src': r'v2\output_실측 물채움\2026-07-23 벌어진 컵 3D프린터(10, 1.5, 3.5)',
        'out_name': '08_3D프린터_벌어진컵_100mm_r15_35mm.json',
        'desc': '2026-07-23 3D프린터 벌어진 컵 (높이 100mm, 바닥r 15mm, 입구r 35mm)',
        'z_pts': np.array([0.0, 0.100]), 'r_pts': np.array([0.015, 0.035])
    },
    {
        'src': r'v2\output_실측 물채움\2026-07-23 벌어진 컵 유리(14.4, 2.5, 4.2)',
        'out_name': '09_유리_벌어진컵_144mm_r25_42mm.json',
        'desc': '2026-07-23 유리 벌어진 컵 (높이 144mm, 바닥r 25mm, 입구r 42mm)',
        'z_pts': np.array([0.0, 0.144]), 'r_pts': np.array([0.025, 0.042])
    },
    {
        'src': r'v2\output_실측 물채움\2026-07-23 벌어진 컵 유리(8.2, 1.7, 2.7)',
        'out_name': '10_유리_벌어진컵_82mm_r17_27mm.json',
        'desc': '2026-07-23 유리 벌어진 컵 (높이 82mm, 바닥r 17mm, 입구r 27mm)',
        'z_pts': np.array([0.0, 0.082]), 'r_pts': np.array([0.017, 0.027])
    },
    {
        'src': r'v2\output_실측 물채움\2026-07-23 일자컵 3D프린터(10, 2.5)',
        'out_name': '11_3D프린터_일자컵_100mm_r25mm.json',
        'desc': '2026-07-23 3D프린터 일자 컵 (높이 100mm, 반지름 25mm)',
        'z_pts': np.array([0.0, 0.100]), 'r_pts': np.array([0.025, 0.025])
    },
    {
        'src': r'v2\output_실측 물채움\2026-07-27 매스실린더(18, 1.1)',
        'out_name': '12_매스실린더_180mm_r11mm.json',
        'desc': '2026-07-27 매스실린더 (높이 180mm, 반지름 11mm)',
        'z_pts': np.array([0.0, 0.180]), 'r_pts': np.array([0.011, 0.011])
    },
    {
        'src': r'v2\output_실측 물채움\2026-07-27 벌어진 컵 고무(11.5, 2.2, 3.8)',
        'out_name': '13_고무_벌어진컵_115mm_r22_38mm.json',
        'desc': '2026-07-27 고무 벌어진 컵 (높이 115mm, 바닥r 22mm, 입구r 38mm)',
        'z_pts': np.array([0.0, 0.115]), 'r_pts': np.array([0.022, 0.038])
    },
    {
        'src': r'v2\output_실측 물채움\2026-07-27 벌어진 컵 유리(8.3, 2, 4)',
        'out_name': '14_유리_벌어진컵_83mm_r20_40mm.json',
        'desc': '2026-07-27 유리 벌어진 컵 (높이 83mm, 바닥r 20mm, 입구r 40mm)',
        'z_pts': np.array([0.0, 0.083]), 'r_pts': np.array([0.020, 0.040])
    },
    {
        'src': r'v2\output_실측 물채움\2026-07-27 벌어진 컵 텀블러(13.8, 2.6, 4)',
        'out_name': '15_텀블러_벌어진컵_138mm_r26_40mm.json',
        'desc': '2026-07-27 텀블러 벌어진 컵 (높이 138mm, 바닥r 26mm, 입구r 40mm)',
        'z_pts': np.array([0.0, 0.138]), 'r_pts': np.array([0.026, 0.040])
    },
    {
        'src': r'v2\output_실측 물채움\2026-07-27 오므라진 컵 유리(9, 3.4)',
        'out_name': '16_유리_오므라진컵_90mm_r34mm.json',
        'desc': '2026-07-27 유리 오므라진 컵 (높이 90mm, 바닥r 38mm, 입구r 28mm, 평균r 34mm)',
        'z_pts': np.array([0.0, 0.090]), 'r_pts': np.array([0.038, 0.028])
    },
    {
        'src': r'v2\output_실측 물채움\2026-07-27 일자컵 유리(15.2, 2.9)',
        'out_name': '17_유리_일자컵_152mm_r29mm.json',
        'desc': '2026-07-27 유리 일자 컵 (높이 152mm, 반지름 29mm)',
        'z_pts': np.array([0.0, 0.152]), 'r_pts': np.array([0.029, 0.029])
    },
    {
        'src': r'v2\output_실측 물채움\2026-08-04 일자컵 (15, 4)',
        'out_name': '18_일자컵_150mm_r40mm.json',
        'desc': '2026-08-04 일자 컵 (높이 150mm, 반지름 40mm)',
        'z_pts': np.array([0.0, 0.150]), 'r_pts': np.array([0.040, 0.040])
    },
    {
        'src': r'v2\output_실측 물채움\2026-08-04 일자컵 (15, 5)',
        'out_name': '19_일자컵_150mm_r50mm.json',
        'desc': '2026-08-04 일자 컵 (높이 150mm, 반지름 50mm)',
        'z_pts': np.array([0.0, 0.150]), 'r_pts': np.array([0.050, 0.050])
    }
]

print("Processing Ring datasets...")
for ds in ring_datasets:
    jfiles = glob.glob(os.path.join(ds['src'], '*.json'))
    if not jfiles: continue
    with open(jfiles[0], encoding='utf-8') as f:
        data = json.load(f)

    z_b, r_v, z_plot, r_plot = make_ring_profile_exact(ds['colors'])
    H_m = float(z_b[-1])
    labels_m, mask = slot_labels_piecewise(z_b, r_v)

    data['name'] = ds['out_name'].replace('.json', '')
    data['description'] = ds['desc']
    data['true_H_m'] = round(H_m, 6)
    data['true_H_mm'] = round(H_m * 1000.0, 2)
    data['true_r_m'] = [round(float(val), 6) for val in labels_m]
    data['true_r_mm'] = [round(float(val) * 1000.0, 2) for val in labels_m]
    data['true_mask'] = [int(m) for m in mask]
    data['true_profile_z_mm'] = [round(float(zv) * 1000.0, 2) for zv in z_plot]
    data['true_profile_r_mm'] = [round(float(rv) * 1000.0, 2) for rv in r_plot]
    data['original_filename'] = os.path.basename(jfiles[0])

    out_path = os.path.join(out_dir, ds['out_name'])
    with open(out_path, 'w', encoding='utf-8') as out_f:
        json.dump(data, out_f, ensure_ascii=False, indent=2)
    print(f"Saved Ring Cup: {ds['out_name']}")

print("\nProcessing Continuous datasets...")
for ds in continuous_datasets:
    jfiles = glob.glob(os.path.join(ds['src'], '*.json'))
    if not jfiles: continue
    with open(jfiles[0], encoding='utf-8') as f:
        data = json.load(f)

    z_pts, r_pts = ds['z_pts'], ds['r_pts']
    H_m = float(z_pts[-1])
    labels_m, mask = slot_labels_continuous(z_pts, r_pts)

    data['name'] = ds['out_name'].replace('.json', '')
    data['description'] = ds['desc']
    data['true_H_m'] = round(H_m, 6)
    data['true_H_mm'] = round(H_m * 1000.0, 2)
    data['true_r_m'] = [round(float(val), 6) for val in labels_m]
    data['true_r_mm'] = [round(float(val) * 1000.0, 2) for val in labels_m]
    data['true_mask'] = [int(m) for m in mask]
    data['true_profile_z_mm'] = [round(float(zv) * 1000.0, 2) for zv in z_pts]
    data['true_profile_r_mm'] = [round(float(rv) * 1000.0, 2) for rv in r_pts]
    data['original_filename'] = os.path.basename(jfiles[0])

    out_path = os.path.join(out_dir, ds['out_name'])
    with open(out_path, 'w', encoding='utf-8') as out_f:
        json.dump(data, out_f, ensure_ascii=False, indent=2)
    print(f"Saved Continuous Cup: {ds['out_name']}")

print("\nALL 20 exact JSON files successfully updated!")
