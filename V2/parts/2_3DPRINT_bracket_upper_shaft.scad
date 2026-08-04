// =========================================================================
// [부품] 상부 축 브래킷 (Upper Shaft Support Bracket)
// 가공: 3D 프린팅 (PLA)
// 원점: 보 상면 = Z=0, 축 중심 = XY 원점
// 특징: 1.0mm 심 와셔(Washer Shim) 삽입 조합 방식의 프레임 조립 오차 정렬 구조
// =========================================================================
include <_params.scad>

BRKT_T = 8.0;
BOTTOM_T = 10.0;
FLOAT_H = BOSS_H + WASHER_T - 10;  // 리볼버 Z 오프셋 (2mm)
UPPER_GAP = 2.0;           // 상단 허브 상면↔바닥판 하면 간격
DROP_H = (Z_TOP - PF) - (FLOAT_H + UPPER_HUB_Z + HUB_H + UPPER_GAP + BOTTOM_T);
BOSS_CLEAR = BOSS_OD + 1.0;
PLATE_W = 50.0;

// 양측 1.0mm 와셔(WASHER_T=1.0mm) 삽입용 유격 (양쪽 1.0mm씩 총 2mm 여유 → 내측 32mm 폭)
Y_CLEARANCE = WASHER_T;                // 1.0mm
INNER_Y_GAP = PF + (Y_CLEARANCE * 2);  // 32.0mm 내측 폭

HALF_GAP = BOSS_CLEAR/2 + 5;

difference() {
    union() {
        // ㅛ 상부: 좌측 탭 (프레임 전방)
        translate([-PLATE_W/2, -INNER_Y_GAP/2 - BRKT_T, 0])
            cube([PLATE_W, BRKT_T, PF]);
        // ㅛ 상부: 우측 탭 (프레임 후방)
        translate([-PLATE_W/2, INNER_Y_GAP/2, 0])
            cube([PLATE_W, BRKT_T, PF]);
        // ㅛ 연결: 좌측 수평 연결판
        translate([-PLATE_W/2, -HALF_GAP - BRKT_T, -BRKT_T])
            cube([PLATE_W, HALF_GAP + BRKT_T - INNER_Y_GAP/2, BRKT_T]);
        // ㅛ 연결: 우측 수평 연결판
        translate([-PLATE_W/2, INNER_Y_GAP/2, -BRKT_T])
            cube([PLATE_W, HALF_GAP + BRKT_T - INNER_Y_GAP/2, BRKT_T]);
        // ㅛ 하부: 좌측 벽
        translate([-PLATE_W/2, -HALF_GAP - BRKT_T, -DROP_H])
            cube([PLATE_W, BRKT_T, DROP_H - BRKT_T]);
        // ㅛ 하부: 우측 벽
        translate([-PLATE_W/2, HALF_GAP, -DROP_H])
            cube([PLATE_W, BRKT_T, DROP_H - BRKT_T]);
        // ㅛ 하부: 바닥판
        translate([-PLATE_W/2, -HALF_GAP - BRKT_T, -DROP_H - BOTTOM_T])
            cube([PLATE_W, (HALF_GAP + BRKT_T) * 2, BOTTOM_T]);
    }
    // 보스 관통홀
    translate([0, 0, -DROP_H - BOTTOM_T - 1]) cylinder(d=BOSS_CLEAR, h=BOTTOM_T + 2);
    
    // ── 프로파일 마운트 체결홀 (M5 체결용 ø5.5mm) ──
    for(dx = [-15, 15]) {
        // 전방 탭
        translate([dx, -INNER_Y_GAP/2 - BRKT_T - 1, PF/2])
            rotate([-90, 0, 0]) cylinder(d=5.5, h=BRKT_T + 2);
        // 후방 탭
        translate([dx, INNER_Y_GAP/2 - 1, PF/2])
            rotate([-90, 0, 0]) cylinder(d=5.5, h=BRKT_T + 2);
    }
}
