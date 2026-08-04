// =========================================================================
// [구매] Z축 모터 + 리드스크류 세트 × 1
// 구매: NEMA17 스테핑모터 + T8 리드스크류(~290mm) + 리드넛
// 메인 파일 z_motor_dummy() + z_moving_parts_assembly() 스크류 부분 복사
// =========================================================================
include <_params.scad>

// NEMA17 모터 본체
color([0.1, 0.1, 0.1]) difference() {
    union() {
        translate([-MOTOR_W/2, -MOTOR_W/2, -40]) cube([MOTOR_W, MOTOR_W, 40]);
        cylinder(d=MOTOR_BOSS_D, h=MOTOR_BOSS_H);
    }
    translate([0, 0, -45]) cylinder(d = SCREW_D + 2, h = 50);
}

// 리드스크류 (ø8 × 280mm)
color([0.9, 0.9, 0.2]) cylinder(d=8, h=280);
