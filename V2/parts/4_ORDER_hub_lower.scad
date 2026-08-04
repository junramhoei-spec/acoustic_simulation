// =========================================================================
// [부품] 하단 허브 (Lower Hub)
// 가공: 레이저커팅 아크릴 5T × 3장 적층 + 하면 모따기 의뢰
// 원점: 허브 하면 = Z=0, 중심 = XY 원점
// =========================================================================
include <_params.scad>

SQ = PF + GLOBAL_TOLERANCE;

difference() {
    union() {
        cylinder(d=CARTRIDGE_OD, h=HUB_H);                    // 메인 디스크
        translate([0, 0, -BOSS_H]) cylinder(d=BOSS_OD, h=BOSS_H);  // 하단 보스
    }
    // 사각 축 소켓 (상면에서 5mm 삽입, 하면은 솔리드)
    translate([-SQ/2, -SQ/2, HUB_H - POCKET_DEPTH]) cube([SQ, SQ, POCKET_DEPTH + 1]);
    // 6× 파이프 소켓 (상면에서 POCKET_DEPTH 삽입, 파이프가 위에서 꽂힘)
    for(a = [0 : 60 : 359]) rotate([0, 0, a])
        translate([REVOLVER_PCD/2, 0, HUB_H - POCKET_DEPTH])
            cylinder(d=ACRYL_OD + GLOBAL_TOLERANCE, h=POCKET_DEPTH + 1);
    // 6× 지컵 관통 (컵 ID, 링 낙하용)
    for(a = [0 : 60 : 359]) rotate([0, 0, a])
        translate([REVOLVER_PCD/2, 0, -1])
            cylinder(d=CUP_ID + 0.5, h=HUB_H + 2);
    // 6× 지컵 하면 모따기 C2 (디스크 하면 Z=0, 링 낙하 가이드)
    for(a = [0 : 60 : 359]) rotate([0, 0, a])
        translate([REVOLVER_PCD/2, 0, -0.1])
            cylinder(d1=CUP_ID + 0.5 + 4, d2=CUP_ID + 0.5, h=2.1);
}
