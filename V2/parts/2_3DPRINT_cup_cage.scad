// =========================================================================
// [부품] 컵 케이지 (Cup Cage / Piston Housing)
// 가공: 3D 프린팅 (PLA) × 1개
// 원점: 케이지 상면(컵 원통 접촉면) = Z=0, 중심 = XY 원점
// 변경: 외경 CUP_OD→SOCK_OD (소켓 일체형 확장)
// =========================================================================
include <_params.scad>

// 아크릴 파이프 소켓 파라미터
SOCK_ID = ACRYL_OD + GLOBAL_TOLERANCE;  // 106.2mm
SOCK_WALL = 5;
SOCK_OD = SOCK_ID + SOCK_WALL * 2;       // 116.2mm
CUP_SOCK_H = 15;  // 컵 외벽 감싸는 소켓 턱 높이

union() {
    // 케이지 본체 + 소켓 턱 (외경=SOCK_OD)
    difference() {
        translate([0, 0, -CAGE_H]) cylinder(d=SOCK_OD, h=CAGE_H + CUP_SOCK_H);
        // 내부 공간 (피스톤 영역)
        translate([0, 0, -CAGE_H + FLOOR_H])
            cylinder(d=CUP_ID, h=CAGE_H - FLOOR_H + 0.1);
        // 소켓 턱 내경 (컵 OD110 수용)
        translate([0, 0, 0])
            cylinder(d=CUP_OD + GLOBAL_TOLERANCE, h=CUP_SOCK_H + 0.1);
        // 측면 개구부 (냉각/접근)
        translate([-32.5, -SOCK_OD/2 - 10, -CAGE_H + FLOOR_H + 5])
            cube([65, SOCK_OD + 20, CAGE_H - FLOOR_H - 10]);
        // 모터 보스 관통
        translate([0, 0, -CAGE_H - 0.1])
            cylinder(d = MOTOR_BOSS_D + GLOBAL_TOLERANCE, h = FLOOR_H + 0.2);
        // NEMA 17 볼트홀
        for(x = [-MOTOR_PITCH/2, MOTOR_PITCH/2])
            for(y = [-MOTOR_PITCH/2, MOTOR_PITCH/2])
                translate([x, y, -CAGE_H - 1])
                    cylinder(d = MOTOR_HOLE_D, h = FLOOR_H + 3);
        // 브래킷 마운트홀
        for(a = [45, 135, 225, 315])
            rotate([0, 0, a]) translate([Z_MOUNT_PCD/2, 0, -CAGE_H - 1])
                cylinder(d = 4.5, h = FLOOR_H + 2);
        // 배수 드레인
        translate([0, 0, -CAGE_H + FLOOR_H + LEAK_DRAIN_D/2])
            rotate([0, -90, 0])
                cylinder(d = LEAK_DRAIN_D, h = SOCK_OD/2 + 10);
        // 일체형 가이드 부싱 홀 (외경 ø8.0 파이프 가이드용 슬라이딩 공차 적용 ø8.3 관통)
        translate([-DRAIN_RADIUS, 0, -CAGE_H - 1])
            cylinder(d = GUIDE_PIPE_D + 0.3, h = FLOOR_H + 2);
    }
    // 내부 립
    difference() {
        translate([0, 0, -CAGE_H + FLOOR_H])
            cylinder(d=LIP_D, h=LIP_H);
        translate([0, 0, -CAGE_H + FLOOR_H - 0.1])
            cylinder(d = MOTOR_BOSS_D + GLOBAL_TOLERANCE, h = LIP_H + 0.2);
    }
}
