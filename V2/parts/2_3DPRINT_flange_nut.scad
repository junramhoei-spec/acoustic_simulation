// =========================================================================
// [부품] T8 잼 플랜지 너트 (T8 Jam Flange Nut)
// 가공: 3D 프린팅 (PLA) × 1개
// 원점: 플랜지 상면 (피스톤 접촉면) = Z=0, 중심 = XY 원점
// 용도: 피스톤과 T8 리드스크류 결합부 유격 제거 및 이중 너트 고정 (Jam Nut)
// =========================================================================
include <_params.scad>

// T8 4-start 오른나사(Right-handed) 리드스크류 암나사 생성 모듈
module t8_internal_thread_subtraction(h) {
    linear_extrude(height = h, twist = -360 * h / 8, slices = max(30, h * 5), convexity = 10) {
        difference() {
            circle(d = 8.25, $fn = 40);
            for (a = [0, 90, 180, 270]) {
                rotate([0, 0, a]) {
                    polygon(points = [[4.125, -0.65], [4.125, 0.65], [3.35, 0]]);
                }
            }
        }
    }
}

// ── T8 잼 플랜지 너트 ──
module t8_flange_nut() {
    FN_L     = 35;   // 나사부 전장
    FLANGE_D = 50;   // 손조임 플랜지
    FLANGE_T = 6;
    BODY_D   = 17;

    difference() {
        union() {
            cylinder(d = FLANGE_D, h = FLANGE_T, $fn = 120);
            cylinder(d = BODY_D,   h = FN_L,     $fn = 80);
        }
        translate([0, 0, -0.1]) t8_internal_thread_subtraction(FN_L + 0.2);
        // 플랜지 테두리 손가락 홈 12개 (반지림 방향 2mm 깊게 파냄)
        for (a = [0:30:359]) rotate([0, 0, a])
            translate([FLANGE_D/2 + 0.5, 0, -1]) cylinder(d = 7, h = FLANGE_T + 2, $fn = 30);
    }
}

t8_flange_nut();
