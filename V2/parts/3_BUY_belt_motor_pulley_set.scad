// =========================================================================
// [구매] 벨트 구동 모터 + 풀리 세트 (타워 마운트 높이 반영)
// 구매: NEMA17 (42×42×43) + GT2 20T 풀리 + GT2 타이밍벨트
// 원점: 브래킷 바닥면(상판 접촉면) = Z=0, 축 상향
// =========================================================================
include <_params.scad>

FLANGE_Z = 52.0;    // 타워 플랜지 높이 (모터 전면 위치 Z=52mm -> 축 상단 Z=76mm)
MOT_BODY_L = 41.0;  // 실측 NEMA 17 모터 몸통 높이 (41mm)
SHAFT_L = 24;
PULLEY_Z = 67.0;    // GT2 풀리 바닥 Z=67.0mm (플랜지 포함 풀리 상단 Z=75.0mm = 축 상단 Z=76.0mm보다 1.0mm 낮춤)

// ── ① NEMA 17 모터 본체 (전면이 Z=42mm에 안착, 몸통은 아래로 위치) ──
color([0.1, 0.1, 0.1])
    translate([-MOTOR_W/2, -MOTOR_W/2, FLANGE_Z - MOT_BODY_L])
        cube([MOTOR_W, MOTOR_W, MOT_BODY_L]);

// ── ② 모터 보스 (ø22 × 2mm, Z=42mm 상면) ──
color([0.25, 0.25, 0.25])
    translate([0, 0, FLANGE_Z])
        cylinder(d=MOTOR_BOSS_D, h=MOTOR_BOSS_H);

// ── ③ 모터 축 (상면에서 위로 돌출, Z=42~66mm) ──
color([0.7, 0.7, 0.7])
    translate([0, 0, FLANGE_Z])
        cylinder(d=5, h=SHAFT_L);

// ── ④ GT2 20치 풀리 (Z=73.5mm, 벨트 라인 정렬) ──
color([0.8, 0.75, 0.1]) translate([0, 0, PULLEY_Z]) difference() {
    union() {
        cylinder(d=SMALL_PULLEY_OD, h=GT2_BELT_W + 2);
        cylinder(d=SMALL_PULLEY_OD + 4, h=1);               // 하부 플랜지
        translate([0, 0, GT2_BELT_W + 1])
            cylinder(d=SMALL_PULLEY_OD + 4, h=1);           // 상부 플랜지
    }
    translate([0, 0, -1]) cylinder(d=5.2, h=GT2_BELT_W + 4);
}

// ── ⑤ 배선 커넥터 (모터 하면) ──
color([0.9, 0.9, 0.9])
    translate([-6, -5, FLANGE_Z - MOT_BODY_L - 3])
        cube([12, 10, 3]);
