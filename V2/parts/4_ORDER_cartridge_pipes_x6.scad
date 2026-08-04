// =========================================================================
// [구매] 카트리지 아크릴 원통 × 6
// 구매: 아크릴 파이프 OD110 ID100 (벽5) 절단 130mm × 6 — 컵(180)+카트리지(130×6)=960 ≤ 1m
// =========================================================================
include <_params.scad>

PIPE_H = UPPER_HUB_Z + POCKET_DEPTH - (HUB_H - POCKET_DEPTH);

for(i = [0:5]) {
    translate([i * (ACRYL_OD + 10), 0, 0])
        color([0.2, 0.5, 0.8, 0.4]) difference() {
            cylinder(d=ACRYL_OD, h=PIPE_H);
            translate([0, 0, -1]) cylinder(d=ACRYL_ID, h=PIPE_H + 2);
        }
}
