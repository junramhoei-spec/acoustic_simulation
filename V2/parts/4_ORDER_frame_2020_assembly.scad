// =========================================================================
// [외주] 2020 알루미늄 프로파일 프레임 어셈블리 (구버전 참고용)
// 메인 파일 aluminum_profile_frame() 모듈에서 추출
// 기둥 6본 + 하부/중부/레일/상부 보 다수
// =========================================================================
include <_params.scad>

module aluminum_profile_frame() { 
    // ── 기둥 6본 (수직) ──
    color([0.75, 0.75, 0.75]) { 
        translate([X_L, Y_B, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]);
        translate([X_L, Y_F, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); 
        translate([X_M, Y_B, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]);
        translate([X_M, Y_F, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); 
        translate([X_R, Y_B, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]);
        translate([X_R, Y_F, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); 
    } 
    // ── 하부 보 (Z_BOT) ──
    color([0.65, 0.65, 0.65]) { 
        translate([X_L + PF, Y_B, Z_BOT]) cube([X_R - X_L - PF, PF, PF]);
        translate([X_L + PF, Y_F, Z_BOT]) cube([X_R - X_L - PF, PF, PF]); 
        translate([X_L, Y_F + PF, Z_BOT]) cube([PF, Y_B - Y_F - PF, PF]);
        translate([X_R, Y_F + PF, Z_BOT]) cube([PF, Y_B - Y_F - PF, PF]);
        translate([X_M, Y_F + PF, Z_BOT]) cube([PF, Y_B - Y_F - PF, PF]); 
    } 
    // ── 레일 보 (Z_RAIL) ──
    color([0.8, 0.8, 0.8]) { 
        translate([X_L, -Y_OFFSET - PF/2, Z_RAIL]) cube([X_R - X_L + PF, PF, PF]);
        translate([X_L, Y_OFFSET - PF/2, Z_RAIL]) cube([X_R - X_L + PF, PF, PF]); 
        translate([X_L, Y_F + PF, Z_RAIL]) cube([PF, Y_B - Y_F - PF, PF]);
        translate([X_R, Y_F + PF, Z_RAIL]) cube([PF, Y_B - Y_F - PF, PF]);
    } 
    // ── 중부 보 (Z_MID = 상판 하면) ──
    color([0.7, 0.7, 0.7]) { 
        translate([X_L + PF, Y_B, Z_MID]) cube([X_M - X_L - PF, PF, PF]);
        translate([X_L + PF, Y_F, Z_MID]) cube([X_M - X_L - PF, PF, PF]); 
        translate([X_L, Y_F + PF, Z_MID]) cube([PF, Y_B - Y_F - PF, PF]);
        translate([-85, Y_F + PF, Z_MID]) cube([PF, Y_B - Y_F - PF, PF]); 
    } 
    // ── 상부 보 (Z_TOP - PF) ──
    color([0.75, 0.75, 0.75]) { 
        translate([X_L + PF, Y_B, Z_TOP - PF]) cube([X_R - X_L - PF, PF, PF]);
        translate([X_L + PF, Y_F, Z_TOP - PF]) cube([X_R - X_L - PF, PF, PF]); 
        translate([X_L, Y_F + PF, Z_TOP - PF]) cube([PF, Y_B - Y_F - PF, PF]);
        translate([X_M, Y_F + PF, Z_TOP - PF]) cube([PF, Y_B - Y_F - PF, PF]);
        translate([X_R, Y_F + PF, Z_TOP - PF]) cube([PF, Y_B - Y_F - PF, PF]); 
    } 
    // ── 리볼버 축 보 (Y=0 중심) ──
    color([0.65, 0.65, 0.65]) { 
        translate([X_L + PF, -PF/2, Z_TOP - PF]) cube([X_M - X_L - PF, PF, PF]);
    } 
    // ── 측정 브래킷 장착용 가로보 ──
    color([0.75, 0.75, 0.75]) { 
        translate([X_M + PF, -PF/2, Z_TOP - PF]) cube([X_R - X_M - PF, PF, PF]); 
    } 
}

aluminum_profile_frame();
