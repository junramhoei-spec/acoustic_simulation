// =========================================================================
// [구매] 컵 원통 (수조 아크릴 파이프) × 1
// 구매: 아크릴 파이프 OD110 ID100 (벽5) 높이 180mm
// 모따기: 상면 내경 C1 + 상면 외경 C1 (선반가공). 하면 모따기 없음
// =========================================================================
include <_params.scad>

CHAM = 1.0;  // 모따기 C1 (상면만, 내·외경)

color([0.2, 0.5, 0.8, 0.25]) difference() {
    cylinder(d=CUP_OD, h=CUP_H);
    // 보어 관통
    translate([0, 0, -1]) cylinder(d=CUP_ID, h=CUP_H + 2);
    // 상면 내경 모따기 C1 (보어 윗모서리 면취)
    translate([0, 0, CUP_H - CHAM])
        cylinder(d1=CUP_ID, d2=CUP_ID + CHAM*2, h=CHAM + 0.1);
    // 상면 외경 모따기 C1 (외측 윗모서리 면취 — 콘 외측 링 컷)
    translate([0, 0, CUP_H - CHAM])
        difference() {
            cylinder(d=CUP_OD + 4, h=CHAM + 1);
            cylinder(d1=CUP_OD, d2=CUP_OD - CHAM*2, h=CHAM);
        }
}
