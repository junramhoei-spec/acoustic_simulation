// =========================================================================
// [부품] 모터 브래킷 (양측 수직벽 포털 아치형 모터 마운트 브래킷)
// 가공: 3D 프린팅 (PLA)
// 원점: 브래킷 바닥면(상판 접촉면) = Z=0, 모터 축 = XY 원점
// 특징: 좌/우 양측 수직벽(내경 43mm) + 상부 천장(Z=52mm) + 기존 가공 상판 체결 정렬
// =========================================================================
include <_params.scad>

module bracket_motor() {
    BLOCK_W = 45.0;       // Y방향 폭 (45mm)
    LEFT_WALL_T = 5.0;    // 좌측 수직벽 두께 (5mm)
    RIGHT_WALL_T = 7.0;   // 우측 수직벽 두께 (7mm)
    LEFT_X_START = -26.5; // 좌측 수직벽 외단 (-26.5mm)
    LEFT_X_END   = -21.5; // 좌측 수직벽 내단 (-21.5mm -> 42mm 모터 좌단 -21mm와 0.5mm 유격)
    RIGHT_X_START = 21.5; // 우측 수직벽 내단 (+21.5mm -> 42mm 모터 우단 +21mm와 0.5mm 유격)
    RIGHT_X_END   = 28.5; // 우측 수직벽 외단 (+28.5mm)
    FLANGE_Z = 52.0;      // 모터 전면 안착 천장 높이 (Z=52mm -> 축 상단 Z=76mm)
    PLATE_T = 6.0;        // 상부 천장 및 바닥 날개 두께 (6mm)
    TOTAL_H = FLANGE_Z + PLATE_T; // 브래킷 전체 높이 (58mm)
    BRKT_EXT = 30.0;      // 우측 체결 날개 연장 길이 (30mm)

    difference() {
        union() {
            // [1] 상부 천장 플랜지 (X = -26.5 ~ +28.5mm, Y = -22.5 ~ +22.5mm, Z = 52~58mm)
            translate([LEFT_X_START, -BLOCK_W/2, FLANGE_Z])
                cube([RIGHT_X_END - LEFT_X_START, BLOCK_W, PLATE_T]);

            // [2-1] 좌측 수직 지지 벽 (X = -26.5 ~ -21.5mm, Z = 0~52mm, 내경 43mm 확보)
            translate([LEFT_X_START, -BLOCK_W/2, 0])
                cube([LEFT_WALL_T, BLOCK_W, FLANGE_Z]);

            // [2-2] 우측 수직 지지 벽 (X = +21.5 ~ +28.5mm, Z = 0~52mm, 내경 43mm 확보)
            translate([RIGHT_X_START, -BLOCK_W/2, 0])
                cube([RIGHT_WALL_T, BLOCK_W, FLANGE_Z]);

            // [3] 하부 상판 체결 바닥 날개 (X = -26.5 ~ +52.5mm, 두께 6mm)
            translate([LEFT_X_START, -BLOCK_W/2, 0])
                cube([BLOCK_W/2 + BRKT_EXT - LEFT_X_START, BLOCK_W, PLATE_T]);
        }

        // [4] NEMA 17 전면 마운트 관통홀 (31mm 피치, M3 관통)
        for(dx = [-MOTOR_PITCH/2, MOTOR_PITCH/2])
            for(dy = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
                translate([dx, dy, FLANGE_Z - 1]) cylinder(d=MOTOR_HOLE_D, h=PLATE_T + 2, $fn=30);
                // 상면 카운터보어 (M3×10mm 볼트 머리 매립, 깊이 3.5mm)
                translate([dx, dy, TOTAL_H - 3.5]) cylinder(d=6.5, h=4.0, $fn=30);
            }

        // [5] 중앙 축 관통홀 (모터 보스 ø22mm 및 샤프트)
        translate([0, 0, FLANGE_Z - 1]) cylinder(d=MOTOR_BOSS_D + 1, h=PLATE_T + 2, $fn=30);

        // [6] 상판 체결 장공 슬롯 (우측벽 X=+28.5mm와 미세 유격 간섭 0% 정밀 보정, X = +32 ~ +42mm)
        for(dy = [-MOTOR_BOLT_PITCH/2, MOTOR_BOLT_PITCH/2])
            hull() {
                translate([32, dy, -2]) cylinder(d=4.5, h=PLATE_T + 4, $fn=30);
                translate([42, dy, -2]) cylinder(d=4.5, h=PLATE_T + 4, $fn=30);
            }
    }
}

// 단품 직접 실행 시 3D 렌더링
bracket_motor();
