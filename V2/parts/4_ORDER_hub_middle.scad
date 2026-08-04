// =========================================================================
// [부품] 중단 허브 (Middle Hub)
// 가공: 레이저커팅 아크릴 5T × 3장 적층
// 원점: 허브 하면 = Z=0, 중심 = XY 원점
// =========================================================================
include <_params.scad>

difference() {
    union() {
        cylinder(d=CARTRIDGE_OD, h=HUB_H);
        // 벨트 외주 림
        difference() {
            cylinder(d=BIG_PULLEY_OD, h=HUB_H);
            translate([0, 0, -1]) cylinder(d=BIG_PULLEY_OD - 14, h=HUB_H + 2);
        }
    }
    // 사각 축 관통
    translate([-SQ/2, -SQ/2, -1]) cube([SQ, SQ, HUB_H + 2]);
    // 6× 파이프 관통홀
    for(a = [0 : 60 : 359]) rotate([0, 0, a])
        translate([REVOLVER_PCD/2, 0, -1])
            cylinder(d=ACRYL_OD + GLOBAL_TOLERANCE, h=HUB_H + 2);
}
