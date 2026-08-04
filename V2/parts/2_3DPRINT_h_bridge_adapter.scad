// =========================================================================
// [부품] H브릿지 어댑터 플레이트 (X슬라이더 ↔ Z모터 연결)
// 가공: 3D 프린팅 (PLA) × 6개
// 원점: 플레이트 하면 = Z=0, 중심 = XY 원점
// =========================================================================
include <_params.scad>

difference() {
    hull() {
        translate([0, -Y_OFFSET, 0]) cylinder(d = X_BLOCK_L + 10, h = BRKT_H);
        translate([0, 0, 0]) cylinder(d = BRKT_D, h = BRKT_H);
        translate([0, Y_OFFSET, 0]) cylinder(d = X_BLOCK_L + 10, h = BRKT_H);
    }
    // X슬라이더 하부 볼트홀 (M3 체결용 ø3.5mm)
    translate([0, -Y_OFFSET, 0])
        for(x = [-X_PITCH_X/2, X_PITCH_X/2])
            for(y = [-X_PITCH_Y/2, X_PITCH_Y/2])
                translate([x, y, -1]) cylinder(d = 3.5, h = BRKT_H + 2);
    // X슬라이더 상부 볼트홀 (M3 체결용 ø3.5mm)
    translate([0, Y_OFFSET, 0])
        for(x = [-X_PITCH_X/2, X_PITCH_X/2])
            for(y = [-X_PITCH_Y/2, X_PITCH_Y/2])
                translate([x, y, -1]) cylinder(d = 3.5, h = BRKT_H + 2);
    // 중앙 관통홀
    translate([0, 0, -1]) cylinder(d = BRKT_ID, h = BRKT_H + 2);
    // Z모터 마운트홀
    for(a = [45, 135, 225, 315])
        rotate([0, 0, a]) translate([Z_MOUNT_PCD/2, 0, -1])
            cylinder(d = 4.5, h = BRKT_H + 2);
    // 배수 관통
    translate([-DRAIN_RADIUS, 0, -1]) cylinder(d = 14, h = BRKT_H + 2);
}
