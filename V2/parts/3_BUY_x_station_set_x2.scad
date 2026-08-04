// =========================================================================
// [구매] X축 리니어 스테이션 세트 × 2 (전방 Y=-85, 후방 Y=+85)
// 구매: 리니어 레일(290mm) + 슬라이더 + NEMA17 + 리드스크류 + 엔드브래킷 + 커플링
// 메인 파일 x_stage_rail_dummy() + x_slider_block_dummy() 그대로 복사
// =========================================================================
include <_params.scad>

SCREW_CZ = 5;
MOT_BODY_L = 43;
BRKT_T_X = 8;
MOTOR_EXTEND = BRKT_T_X + MOTOR_BOSS_H + MOT_BODY_L + 5;
RAIL_END_X = (X_R + PF) - MOTOR_EXTEND;
RAIL_START_X = RAIL_END_X - X_RAIL_LEN;

// ── ① 알루미늄 레일 프로파일 본체 (40W × 30H) ──
color([0.78, 0.78, 0.78]) difference() {
    translate([RAIL_START_X, -X_RAIL_W/2, -X_RAIL_H/2])
        cube([X_RAIL_LEN, X_RAIL_W, X_RAIL_H]);
    translate([RAIL_START_X - 1, -10, X_RAIL_H/2 - 4])
        cube([X_RAIL_LEN + 2, 20, 5]);
}

// ── ② 리드 스크류 (ø8) ──
color([0.60, 0.60, 0.60])
    translate([RAIL_START_X - 3, 0, SCREW_CZ])
        rotate([0, 90, 0]) cylinder(d=SCREW_D, h=X_RAIL_LEN + 6);

// ── ③ +X 엔드 브래킷 (모터 마운트) ──
color([0.12, 0.12, 0.12]) difference() {
    translate([RAIL_END_X, -X_RAIL_W/2, -X_RAIL_H/2])
        cube([BRKT_T_X, X_RAIL_W, X_RAIL_H + 17]);
    translate([RAIL_END_X - 1, 0, SCREW_CZ])
        rotate([0, 90, 0]) cylinder(d=12, h=BRKT_T_X + 2);
}

// ── ④ NEMA 17 스테퍼 모터 ──
translate([RAIL_END_X + BRKT_T_X, 0, SCREW_CZ]) {
    color([0.25, 0.25, 0.25])
        rotate([0, 90, 0]) cylinder(d=MOTOR_BOSS_D, h=MOTOR_BOSS_H);
    color([0.15, 0.15, 0.15])
        translate([MOTOR_BOSS_H, -MOTOR_W/2, -MOTOR_W/2])
            cube([MOT_BODY_L, MOTOR_W, MOTOR_W]);
    color([0.9, 0.9, 0.9])
        translate([MOTOR_BOSS_H + MOT_BODY_L, -6, -5])
            cube([5, 12, 10]);
}

// ── ⑤ 축 커플링 (블루 알루미늄) ──
color([0.1, 0.45, 0.8])
    translate([RAIL_END_X - 5, 0, SCREW_CZ])
        rotate([0, 90, 0]) cylinder(d=16, h=16);

// ── ⑥ -X 엔드 브래킷 (베어링 서포트) ──
color([0.12, 0.12, 0.12]) difference() {
    translate([RAIL_START_X - BRKT_T_X, -X_RAIL_W/2, -X_RAIL_H/2])
        cube([BRKT_T_X, X_RAIL_W, X_RAIL_H + 8]);
    translate([RAIL_START_X - BRKT_T_X - 1, 0, SCREW_CZ])
        rotate([0, 90, 0]) cylinder(d=10, h=BRKT_T_X + 2);
}

// ── ⑦ 캐리지 슬라이더 블록 ──
color([0.2, 0.2, 0.2]) difference() {
    translate([-X_BLOCK_L/2, -X_BLOCK_W/2, X_RAIL_H/2])
        cube([X_BLOCK_L, X_BLOCK_W, X_TOTAL_H - X_RAIL_H]);
    for(x = [-X_PITCH_X/2, X_PITCH_X/2])
        for(y = [-X_PITCH_Y/2, X_PITCH_Y/2])
            translate([x, y, X_RAIL_H/2 - 1]) cylinder(d=3.5, h=12);
}
// 리드넛 하우징
color([0.18, 0.18, 0.18])
    translate([-12, -10, SCREW_CZ - 10]) cube([24, 20, 15]);
// 가이드 슈
color([0.15, 0.15, 0.15])
    for(sy = [-1, 1])
        translate([-X_BLOCK_L/2, sy * 15 - 5, X_RAIL_H/2 - 5])
            cube([X_BLOCK_L, 10, 5]);
