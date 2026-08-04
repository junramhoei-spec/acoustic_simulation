// =========================================================================
// [부품] 측정 브래킷 (Acoustic Measurement Bracket) — 3030 프레임 대응
// 가공: 3D 프린팅 (PLA) × 1개
// 원점: 보 하면(볼팅면) = Z=0, 중심 = XY 원점
// 포함: 스피커 슈라우드(보 하면까지 직접 연장), 좌우 날개 체결(X대칭),
//       마이크 가이드, 급수관 노즐 일체형
// X_POS_MEASURE=170 → X_M 보(-110~-80), X_R 보(+80~+110), 볼트 ±95
// =========================================================================
include <_params.scad>

TOL = 0.3;

// 스피커 치수
SPK_OD=106;  SPK_CUT=102;  SPK_PCD=116;
SPK_DEPTH=55;  SPK_HOLE=5;  SPK_FT=3;

// 마이크/급수
MIC_D=22;  MIC_TD=7;
TUBE_OD=8;

// 브래킷
WALL = 8;        // 슈라우드 벽 두께 (강화, 날개 직결 구조)
FW=120;  FCR=10;
PKT_W = FW + TOL*2;   PKT_CR = FCR + TOL;
SHR_W = PKT_W + WALL*2; SHR_CR = PKT_CR + WALL;  // 136.6×136.6, R=18.3
SH_EXT = SHR_W / 2;

SPK_Z  = -SPK_DEPTH;            // -55 (하면 결합, 상판 판재 없음)
SH_BOT = SPK_Z - WALL;          // -63
SH_H   = -SH_BOT;              // 63 (z=0까지 직접 연장)
MP_Z = SH_BOT;

MIC_ANG  = 35;
MIC_PRO  = (MP_Z + 180) / cos(MIC_ANG);
MIC_Y    = -MIC_PRO * sin(MIC_ANG);

TP_Z = MP_Z;
TUBE_ANG = atan((65 - 35) / (TP_Z + 165));
TUBE_Y   = 35 + (TP_Z + 165) * tan(TUBE_ANG);
NOZZLE_EXIT_Z = -155;
NOZZLE_AXIS_L = (TP_Z - NOZZLE_EXIT_Z) / cos(TUBE_ANG);

difference() {
    union() {
        // ① 스피커 라운드사각 슈라우드 (보 하면 z=0까지 직접 연장)
        translate([0, 0, SH_BOT]) hull() {
            for(sx=[-1,1]) for(sy=[-1,1])
                translate([sx*(SHR_W/2-SHR_CR), sy*(SHR_W/2-SHR_CR), 0])
                    cylinder(r=SHR_CR, h=SH_H);
        }
        // ①-a 좌측 보 체결 날개 (슈라우드 → X_M 보, 대칭)
        hull() {
            translate([-(SHR_W/2), -28, -WALL]) cube([1, 56, WALL]);
            translate([-110, -28, -WALL]) cube([30, 56, WALL]);
        }
        // ①-b 우측 보 체결 날개 (슈라우드 → X_R 보, 대칭)
        hull() {
            translate([SHR_W/2 - 1, -28, -WALL]) cube([1, 56, WALL]);
            translate([80, -28, -WALL]) cube([30, 56, WALL]);
        }
        // ③ 마이크 가이드 브릿지
        hull() {
            translate([0, -SH_EXT, MP_Z-15]) cylinder(d=25, h=30);
            translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0])
                translate([0,0,-20]) cylinder(d=MIC_D+14, h=65);
        }
        // ③-b 마이크 클램프 귀
        translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0]) {
            translate([0.75, -(18+10), 5]) cube([10, 10, 25]);
            translate([-(0.75+10), -(18+10), 5]) cube([10, 10, 25]);
        }
        // ④ 급수관 가이드 브릿지
        hull() {
            translate([0, SH_EXT, TP_Z-10]) cylinder(d=18, h=20);
            translate([0, TUBE_Y, TP_Z]) rotate([-TUBE_ANG,0,0])
                translate([0,0,-15]) cylinder(d=TUBE_OD+14, h=55);
        }
        // ⑤ 급수관 노즐
        translate([0, TUBE_Y, TP_Z]) rotate([-TUBE_ANG,0,0])
            translate([0, 0, -NOZZLE_AXIS_L]) cylinder(d=TUBE_OD+6, h=NOZZLE_AXIS_L-15);
    }
    // ① M5 볼트 관통 (Y방향 보 T슬롯 직결, 날개 관통, ±95 대칭)
    for(y = [-12, 12]) {
        // X_M 보 (local x = -95, 대칭)
        translate([-95, y, -WALL-1]) cylinder(d=5.5, h=WALL+2);
        translate([-95, y, -WALL-1]) cylinder(d=10, h=4);
        // X_R 보 (local x = +95, 대칭)
        translate([95, y, -WALL-1]) cylinder(d=5.5, h=WALL+2);
        translate([95, y, -WALL-1]) cylinder(d=10, h=4);
    }
    // 음파 개구
    translate([0, 0, SH_BOT-1]) cylinder(d=96, h=WALL+1);
    // 스피커 포켓 (하면에서 삽입)
    translate([0, 0, SPK_Z]) hull() {
        for(sx=[-1,1]) for(sy=[-1,1])
            translate([sx*(PKT_W/2-PKT_CR), sy*(PKT_W/2-PKT_CR), 0])
                cylinder(r=PKT_CR, h=SPK_DEPTH+5);
    }
    // 스피커 나사
    for(a = [45, 135, 225, 315]) rotate([0,0,a])
        translate([SPK_PCD/2, 0, SH_BOT-1])
            cylinder(d=SPK_HOLE+0.5, h=WALL+SPK_FT+2);
    // 배선 관통 (하부, 마그넷 옆)
    translate([0, 0, SPK_Z+SPK_DEPTH-2]) cylinder(d=40, h=WALL+5);
    // 마이크 보어
    translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0]) {
        cylinder(d=MIC_TD+TOL*2, h=500, center=true);
        translate([0,0,-40]) cylinder(d=MIC_D+TOL*2, h=250);
    }
    // 클램프 슬릿
    translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0])
        translate([-0.75, -30, -22]) cube([1.5, 31, 69]);
    // 클램프 볼트
    translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0])
        translate([0, -23, 17.5]) rotate([0,90,0])
            cylinder(d=4.3, h=40, center=true);
    // 급수관 보어
    translate([0, TUBE_Y, TP_Z]) rotate([-TUBE_ANG,0,0])
        cylinder(d=TUBE_OD+TOL, h=500, center=true);
    // 보 영역 클리핑
    translate([-115, -120, 0]) cube([230, 240, 80]);
}
