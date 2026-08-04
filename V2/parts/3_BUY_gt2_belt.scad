// =========================================================================
// [구매] GT2 타이밍 벨트
// 구매: GT2 6mm 폭 오픈 벨트, 필요 길이 산출
// 큰 풀리(하단 허브 외주 550T) ↔ 작은 풀리(모터 20T) 연결
// =========================================================================
include <_params.scad>

// 벨트 경로 계산
// 모터 위치: (BELT_MOTOR_X, BELT_MOTOR_Y) 기준, 리볼버 축: (-REVOLVER_PCD/2, 0)
DX = BELT_MOTOR_X - (-REVOLVER_PCD/2);
DY = BELT_MOTOR_Y - 0;
CENTER_DIST = sqrt(DX*DX + DY*DY);
BELT_T = 1.5;  // 벨트 두께

// 간이 벨트 시각화 (두 풀리 간 직선 + 풀리 외주 감김)
color([0.15, 0.15, 0.15, 0.7]) {
    // 큰 풀리 감김 (중단 허브 외주)
    translate([0, 0, 0]) difference() {
        cylinder(d=BIG_PULLEY_OD + BELT_T*2, h=GT2_BELT_W);
        translate([0, 0, -1]) cylinder(d=BIG_PULLEY_OD, h=GT2_BELT_W + 2);
    }
    // 작은 풀리 감김 (모터)
    translate([CENTER_DIST, 0, 0]) difference() {
        cylinder(d=SMALL_PULLEY_OD + BELT_T*2, h=GT2_BELT_W);
        translate([0, 0, -1]) cylinder(d=SMALL_PULLEY_OD, h=GT2_BELT_W + 2);
    }
    // 직선 구간 (상하 2개)
    R1 = BIG_PULLEY_OD/2;
    R2 = SMALL_PULLEY_OD/2;
    // 상부 직선
    translate([R2, R2 + BELT_T/2, 0])
        cube([CENTER_DIST - R2, BELT_T, GT2_BELT_W]);
    // 하부 직선
    translate([R2, -(R2 + BELT_T/2 + BELT_T), 0])
        cube([CENTER_DIST - R2, BELT_T, GT2_BELT_W]);
}
