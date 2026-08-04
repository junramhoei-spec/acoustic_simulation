// =========================================================================
// [부품] 컵 피스톤 (Cup Piston)
// 가공: 3D 프린팅 (PLA) × 1개
// 원점: 피스톤 상면(수면 접촉면) = Z=0, 중심 = XY 원점
// 포함: 오링 홈 (홈 바닥 ø93.0, 폭 4.8mm), 3D 프린팅용 일체형 T8 암나사 (접착 고정용)
// =========================================================================
include <_params.scad>

// 오링 파라미터 (홈 바닥 ø93.0mm, 홈 폭 4.8mm)
ORING_W = 4.8;        // 오링 홈 폭 (4.8mm)
ORING_GROOVE_D = 93.0;// 홈 바닥 지름 (ø93.0mm)
ORING_Z = 10.0;       // 홈 중심 위치 (피스톤 상면에서 Z=-10)

// T8 4-start 오른나사(Right-handed) 리드스크류 암나사 생성 모듈
// 규격: 외경 8.0mm, 리드 8.0mm, 피치 2.0mm (4줄 오른나사, 90° 대칭, 1회전 8mm 이동)
module t8_internal_thread_subtraction(h) {
    // OpenSCAD에서 표준 오른나사(Right-handed thread)를 생성하려면 twist에 음수(-)를 적용해야 합니다.
    // (+값 적용 시 왼나사/Left-handed가 생성되어 시중 T8 리드스크류와 나사산 방향이 반대로 엇갈림)
    linear_extrude(height = h, twist = -360 * h / 8, slices = max(30, h * 5), convexity = 10) {
        difference() {
            circle(d = 8.25, $fn = 40);
            for (a = [0, 90, 180, 270]) {                      // 4줄 나사산 (90° 대칭 4개 시작점)
                rotate([0, 0, a]) {
                    // 내향 삼각형 돌기 (피치 2mm 대응, 외경 ø8.25, 이빨끝 R3.35)
                    polygon(points = [[4.125, -0.65], [4.125, 0.65], [3.35, 0]]);
                }
            }
        }
    }
}

difference() {
    union() {
        // 피스톤 본체 (외경 ø98.8mm로 변경하여 유격 최적화)
        translate([0, 0, -PISTON_H]) cylinder(d=98.8, h=PISTON_H);
        // 배수구 하부 가이드 보스 (Boss)
        translate([-DRAIN_RADIUS, 0, -PISTON_H - 10])
            cylinder(d=15, h=10);
    }
    // 3D 프린팅 일체형 T8 나사산 (상면 Z=0 에서 5mm 남기고 진입)
    translate([0, 0, -PISTON_H - 0.1])
        t8_internal_thread_subtraction(PISTON_H - 5 + 0.1);
        
    // 배수관 단턱 소켓 (Z=-5 ~ 0 은 ø6.0 관통, Z=-30 ~ -5 은 ø8.2 소켓)
    translate([-DRAIN_RADIUS, 0, -5])
        cylinder(d=6.0, h=6.1);
    translate([-DRAIN_RADIUS, 0, -PISTON_H - 10 - 1])
        cylinder(d=DRAIN_D + GLOBAL_TOLERANCE, h=PISTON_H + 10 - 5 + 1.1);
        
    // 오링 홈 (외주면 1줄, 홈 바닥 ø93.0mm, 홈 폭 4.8mm)
    translate([0, 0, -ORING_Z - ORING_W/2]) difference() {
        cylinder(d = CUP_ID + 2, h = ORING_W);
        translate([0, 0, -0.5]) cylinder(d = ORING_GROOVE_D, h = ORING_W + 1);
    }
    
    // ── 피스톤 상면 배수 유로 홈 (Water Channel) ──
    // 음향 공명에 방해를 주지 않도록 중앙에서 7mm 떨어진 위치부터 배수구(X=-35) 방향으로 향하는 1줄의 홈만 형성 (폭 4mm, 깊이 3mm)
    rotate([0, 0, 180]) translate([7, -2, -3]) cube([DRAIN_RADIUS - 7 + 2, 4, 3.1]);
}
