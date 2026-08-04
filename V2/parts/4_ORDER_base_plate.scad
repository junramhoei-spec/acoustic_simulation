// =========================================================================
// [부품] 상판 (Upper Fixed Base Plate)
// 가공: 아크릴 15T 통판 (보스홀 ⌀36 깊이 10mm 비관통 단가공)
// 원점: 상판 상면 = Z=0, XY = 메인 어셈블리 원점 동일
// =========================================================================
include <_params.scad>

difference() {
    translate([X_L, Y_F, -TOP_PLATE_H])
        cube([(X_M + PF) - X_L, (Y_B + PF) - Y_F, TOP_PLATE_H]);
    // 기둥 회피홈 (4곳, 정확히 PF=30mm — kerf로 자연 여유 확보)
    translate([X_L - 1, Y_B - 1, -TOP_PLATE_H - 1])
        cube([PF + 1, PF + 1, TOP_PLATE_H + 2]);
    translate([X_L - 1, Y_F - 1, -TOP_PLATE_H - 1])
        cube([PF + 1, PF + 1, TOP_PLATE_H + 2]);
    translate([X_M, Y_B - 1, -TOP_PLATE_H - 1])
        cube([PF + 1, PF + 1, TOP_PLATE_H + 2]);
    translate([X_M, Y_F - 1, -TOP_PLATE_H - 1])
        cube([PF + 1, PF + 1, TOP_PLATE_H + 2]);
    // 컵 관통 개구부 (적재축 DROP_X=+5에 정렬)
    translate([DROP_X, -(CUP_OD + 1)/2, -TOP_PLATE_H - 1])
        cube([CARTRIDGE_OD, CUP_OD + 1, TOP_PLATE_H + 2]);
    translate([DROP_X, 0, -TOP_PLATE_H - 1])
        cylinder(d=CUP_OD + 1, h=TOP_PLATE_H + 2);
    // 하단 보스 수용 블라인드홀 (REVOLVER_CX=판 중심=리볼버 축에 정렬)
    translate([REVOLVER_CX, 0, -10.1])
        cylinder(d=36, h=10.2);
    // 모터 브래킷 체결홀 (X 2열: 55=기본, 40=좌측이동 / Y피치 25)
    for(hx = [MOTOR_BOLT_X_NOMINAL, MOTOR_BOLT_X_SHIFT])
        for(hy = [BELT_MOTOR_Y - MOTOR_BOLT_PITCH/2, BELT_MOTOR_Y + MOTOR_BOLT_PITCH/2])
            translate([hx, hy, -TOP_PLATE_H - 1])
                cylinder(d=4.5, h=TOP_PLATE_H + 2);
}
