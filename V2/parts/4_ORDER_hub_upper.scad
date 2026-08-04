// =========================================================================
// [부품] 상단 허브 (Upper Hub)
// 가공: 레이저커팅 아크릴 5T × 3장 적층
// 원점: 허브 하면 = Z=0, 중심 = XY 원점
// 상부 보스 (축 브래킷 지지) + 하부 파이프 소켓 (파이프에 얹힘)
// =========================================================================
include <_params.scad>

difference() {
    union() {
        cylinder(d=CARTRIDGE_OD, h=HUB_H);                    // 메인 디스크
        // 상부 보스 (축 브래킷 지지)
        translate([0, 0, HUB_H]) cylinder(d=BOSS_OD, h=BOSS_H);
    }
    // 사각 축 관통
    translate([-SQ/2, -SQ/2, -1]) cube([SQ, SQ, HUB_H + BOSS_H + 2]);
    // 6× 파이프 소켓 (하면에서 POCKET_DEPTH 삽입 → 파이프에 얹힘)
    for(a = [0 : 60 : 359]) rotate([0, 0, a])
        translate([REVOLVER_PCD/2, 0, -1])
            cylinder(d=ACRYL_OD + GLOBAL_TOLERANCE, h=POCKET_DEPTH + 1);
    // 6× 지컵 관통
    for(a = [0 : 60 : 359]) rotate([0, 0, a])
        translate([REVOLVER_PCD/2, 0, -1])
            cylinder(d=CUP_ID + 0.5, h=HUB_H + BOSS_H + 2);
}
