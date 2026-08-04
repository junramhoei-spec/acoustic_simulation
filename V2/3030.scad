// =========================================================================
// [갠트리 가변 내부 형상 측정 시스템] 3030 프레임 변환판 (스피커 형상 수정본)
// 기준 원점 (0,0,0) = X축 최좌측 상태의 컵 원통 윗면 중심 및 피스톤 플랫 일치
// 교정 완료: 스피커 더미가 관통 파이프처럼 보이던 기하학적 에러 완벽 수정 (후면 마그넷 폐쇄)
// =========================================================================

$fn = 40; 
GLOBAL_TOLERANCE = 0.2;

// --- [1] 하부 기성품 및 원통 파라미터 세팅 ---
X_RAIL_LEN = 290.0;  // 모터 끝 = 프레임 우측면 일치 기준 (기존 350에서 단축)
X_BLOCK_W = 42.0; X_BLOCK_L = 59.0;
X_PITCH_X = 20.0; X_PITCH_Y = 32.0;
X_RAIL_W = 40.0;  X_RAIL_H = 30.0;

MOTOR_W = 42.0;      MOTOR_PITCH = 31.0; MOTOR_HOLE_D = 3.5;    
MOTOR_BOSS_D = 22.0; MOTOR_BOSS_H = 2.0; SCREW_D = 8.0;         

CUP_ID = 100.0;  CUP_WALL = 5.0; CUP_OD = 110.0;     // 아크릴 원통 OD110/ID100 (유패킹 외경100 기준)
CUP_H = 180.0;   CAGE_H = 60.0;  FLOOR_H = 10.0; PISTON_H = 20.0;     

LIP_D = 30.0;    LIP_H = 5.0;    LEAK_DRAIN_D = 4.0;    
GUIDE_PIPE_D = 8.0; BUSHING_OD = 12.0; BUSHING_H = 8.0;       
DRAIN_RADIUS = 35.0; DRAIN_D = 8.0;        

Y_OFFSET = 85.0; BRKT_H = 12.0; BRKT_D = 122.0; BRKT_ID = 62.0; Z_MOUNT_PCD = 86.0;   

// --- [2] 기성 아크릴 파이프 및 상부 카트리지 파라미터 ---
ACRYL_ID = 100.0; ACRYL_T = 5.0; ACRYL_OD = ACRYL_ID + (ACRYL_T * 2);  // OD110 (아크릴집 106 재고없음 → 컵과 동일 규격)

REVOLVER_PCD = 240.0;     // 인접 카트리지 웹 9.8mm 확보 (OD110 대응, 230→240)
CARTRIDGE_OD = REVOLVER_PCD + ACRYL_OD + 8; 
TOP_PLATE_H = 15.0;       // 5T × 3장 레이저커팅 적층 (단 깊이 10mm)

HUB_D = 60.0;            
SHAFT_D = 12.0;          
HUB_WALL = 4.0;          
HUB_H = 15.0;             // 아크릴 5T × 3장 적층 (레이저커팅) — 파이프 130mm 대응
POCKET_DEPTH = 5.0;        // 10mm 허브 안의 파이프 삽입 깊이
MID_HUB_Z = 68.5;          // 중단 허브 하면 Z (68.5+15/2=76, FLOAT_H=2 보정으로 절대좌표 유지)
UPPER_HUB_Z = 135.0;       // 상단 허브 하면 Z (전체 높이 135+15=150 유지)
BOSS_OD = 35.0;            // 센터링 보스 외경 (아크릴 접착)
BOSS_H = 11.0;             // 보스11 + 와셔1 = 12mm, 리세스10mm → 허브 2mm 공중 (저마찰)

// --- [3] GT2 타이밍 벨트 구동 시스템 파라미터 ---
GT2_PITCH     = 2.0;           // GT2 벨트 피치 (mm)
GT2_BELT_W    = 6.0;           // 벨트 폭 (mm)
BIG_PULLEY_TEETH = 566;        // 큰 풀리 치수 (PCD 230 대응, OD≈361)
BIG_PULLEY_PD = BIG_PULLEY_TEETH * GT2_PITCH / PI;  // ~350mm pitch circle
BIG_PULLEY_OD = BIG_PULLEY_PD + 1.0;                // 외경
SMALL_PULLEY_TEETH = 20;       // 모터 풀리 치수
SMALL_PULLEY_PD = SMALL_PULLEY_TEETH * GT2_PITCH / PI;  // ~12.7mm
SMALL_PULLEY_OD = SMALL_PULLEY_PD + 1.0;
BELT_RATIO = BIG_PULLEY_TEETH / SMALL_PULLEY_TEETH;  // 27.5:1 -> 0.065 deg/step

BELT_MOTOR_X = -300;           // 모터 좌측면 = 상판 좌측면(X_L=-325) 정렬, 감김각 개선
BELT_MOTOR_Y = -155.5;         // 기둥 상단(-180)과 브래킷 하단(-178) 간 2mm 여유
BRKT_MOTOR_H = 25.0;           // 모터 브래킷 높이 (장력 조절용 두꺼운 블록)
BRKT_MOTOR_W = 45.0;           // 브래킷 폭 (NEMA17 42mm + 3mm 여유)
SLOT_LEN = 10.0;              // 장력 조절 슬롯 길이
FLAG_W = 15.0;  FLAG_H = 8.0;  FLAG_T = 1.5;  // 포토 인터럽터 플래그

X_POS_MEASURE = 170.0;   // 측정 브래킷 X좌표 (X_M~X_R 정중앙, X대칭)

// --- [4] 글로벌 3030 프레임 경계 파라미터 ---
// ※ 외곽 치수 600×430×710mm (PCD/풀리 확장 대응)
PF = 30;             // 3030 알루미늄 프로파일
SHAFT_SQ = 20;       // 2020 사각 회전축 (프레임과 독립)
WASHER_T = 1.0;     

X_L = -320;          // 좌측 (외곽 -320, 모터 여유+감김각 개선)
X_M = 60;            // 중간 (외곽 +90 유지: 60+30=90)
X_R = 250;           // 우측 (외곽 +280 유지: 250+30=280)
Y_F = -210;          // 전방 (대칭: -210+30=-180, Y=0 중심)
Y_B = 180;           // 후방 (대칭: 180+30=210, Y=0 중심)

Z_BOT = -480;       // 바닥 (보 상면 -450, 스크류 하단 -440과 10mm 여유)
Z_RAIL = -322;      // 레일 (보 상면 -292 유지: -322+30=-292)
Z_MID = -TOP_PLATE_H - PF;  // 상판 하면에 맞춤 (-45)
Z_TOP = 220;        // 상단 (보 하면 190 유지: 220-30=190)

SUPPORT_PILLAR_H = Z_TOP - PF;

// --- 리볼버/컵 축 정렬 (보스홀=판 중심에 리볼버 정렬) ---
REVOLVER_CX = (X_L + X_M + PF)/2;            // 판 중심 = 보스홀 = 리볼버 회전축 (-115)
DROP_X      = REVOLVER_CX + REVOLVER_PCD/2;  // 링 드롭 / 컵 적재 축 (+5)

// --- 모터 체결홀 (베이스 플레이트 ↔ 모터 브래킷 슬롯 공유) ---
MOTOR_BOLT_PITCH     = 25;        // Y피치 (모터축 기준 ±12.5)
MOTOR_BOLT_X_NOMINAL = X_L + 55;  // 1열: 판 좌단 55 (모터 기본 위치)
MOTOR_BOLT_X_SHIFT   = X_L + 40;  // 2열: 판 좌단 40 (모터 좌측 이동 대비)

// 모터 마운트 볼트 카운터보어 (단볼트용 — 브래킷 두께 25 중 깊게 파냄)
MOTOR_CB_D     = 6.5;             // M3 캡볼트 머리 클리어런스
MOTOR_CB_DEPTH = 19;              // 카운터보어 깊이 (잔여 통과 6mm → M3×10 단볼트)

// =========================================================================
// [일반화 동적 시퀀스 엔진] 임의의 STACK_ORDER 지원
// =========================================================================
STACK_ORDER = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1];  // 슬롯0 ×5 → 슬롯1 ×5 (임의 조합 가능)
N_STACK = len(STACK_ORDER);  // 총 드롭 링 개수
RH = 15;  // 링 높이 (mm)
RING_OD = 99.4;  // 3D 프린터 수축 보정을 고려해 99.4mm로 수정된 외경 (mm)

// ── 링 데이터 (전역 상수) ──
RING_IDS = [20, 32, 44, 56, 68, 80];
RING_CLRS = [[1,0,0], [1,0.6,0], [1,1,0], [0,1,0], [0,0,1], [0.5,0,0.8]];

// ── 리볼버 부상 높이 (전역) ──
FLOAT_H = BOSS_H + WASHER_T - 10;  // 2mm (보스11 + 와셔1 - 단10)

// ── 동적 유도 도우미 함수 ──
// 리스트의 값을 합산하는 재귀 함수
function sum_list(list, idx=0) =
    (idx >= len(list)) ? 0 : list[idx] + sum_list(list, idx + 1);

// 특정 인덱스 k 이전에 발생한 누적 회전 횟수 구함
function get_rot_count_before(stack, k) =
    (k <= 0) ? 0 :
    len([for(i = [1 : k]) if(stack[i] != stack[i-1]) 1]);

// ── Customizer 수동 제어 슬라이더 (Window -> Customizer 메뉴 활성화 필요) ──
/* [Simulation Control] */
manual_t = 0.0; // [0.0 : 0.005 : 1.0]

// Animate 모드 활성화 시에는 $t 사용, 그렇지 않으면 수동 슬라이더 manual_t 사용
t_val = ($t > 0 && $t < 1) ? $t : manual_t;

// ── 동적 페이즈 산출 ──
TOTAL_ROT = get_rot_count_before(STACK_ORDER, N_STACK - 1);
ANIM_DOWN = N_STACK + TOTAL_ROT;
ANIM_MID  = 6;  // 중간 측정 (고정)
ANIM_UP   = ANIM_DOWN;  // 복귀 (대칭)
ANIM_N    = ANIM_DOWN + ANIM_MID + ANIM_UP;

anim_phase = min(floor(t_val * ANIM_N), ANIM_N - 1);
anim_pt = (t_val * ANIM_N) - anim_phase;
anim_s = (1 - cos(anim_pt * 180)) / 2;  // ease-in-out

// ── 피스톤 Z축 하강 분량 ──
_down_frac =
    (anim_phase < ANIM_DOWN) ? (
        sum_list([for(k = [0 : N_STACK-1])
            let(dp = k + get_rot_count_before(STACK_ORDER, k))
            (anim_phase > dp) ? 1 :
            (anim_phase == dp) ? anim_s :
            0
        ])
    ) :
    (anim_phase < ANIM_DOWN + ANIM_MID) ? N_STACK :
    N_STACK;

// ── 피스톤 Z축 상승 복귀 분량 ──
_up_frac =
    (anim_phase < ANIM_DOWN + ANIM_MID) ? 0 :
    (anim_phase >= ANIM_DOWN + ANIM_MID + ANIM_UP) ? N_STACK :
    let(p_up = anim_phase - (ANIM_DOWN + ANIM_MID))
    sum_list([for(k = [0 : N_STACK-1])
        let(
            dp = k + get_rot_count_before(STACK_ORDER, k),
            up_dp_start = ANIM_UP - 1 - dp
        )
        (p_up > up_dp_start) ? 1 :
        (p_up == up_dp_start) ? anim_s :
        0
    ]);

// ── 측정 중 피스톤 5mm 추가 하강 변위 ──
Z_MEASURE_ADD =
    (anim_phase >= ANIM_DOWN && anim_phase < ANIM_DOWN + ANIM_MID) ? (
        let(mp = anim_phase - ANIM_DOWN)
        (mp == 0) ? 0 :                   // ph 11 (이동 중)
        (mp == 1) ? -5 * anim_s :         // ph 12 (5mm 추가 하강 시작)
        (mp >= 2 && mp <= 4) ? -5 :       // ph 13~15 (5mm 추가 하강 유지)
        (mp == 5) ? -5 * (1 - anim_s) : 0 // ph 16 (원래 높이 복귀)
    ) : 0;

Z_MOVE = -RH * (_down_frac - _up_frac) + Z_MEASURE_ADD;

// ── X축 원통 이동 (DROP_X=적재 위치, X_POS_MEASURE=측정 위치) ──
_mid_ph = anim_phase - ANIM_DOWN;
X_MOVE =
    (anim_phase < ANIM_DOWN) ? DROP_X :
    (anim_phase >= ANIM_DOWN + ANIM_MID) ? DROP_X :
    (_mid_ph == 0) ? DROP_X + (X_POS_MEASURE - DROP_X) * anim_s :
    (_mid_ph >= 1 && _mid_ph <= 4) ? X_POS_MEASURE :
    (_mid_ph == 5) ? DROP_X + (X_POS_MEASURE - DROP_X) * (1 - anim_s) : DROP_X;

// ── 동적 각도 유도 함수 ──
function get_interpolated_ang(dps, p, ease, idx=0) =
    (idx >= N_STACK - 1) ? -STACK_ORDER[N_STACK-1] * 60 :
    (p >= dps[idx] && p < dps[idx+1]) ? (
        let(
            ang_start = -STACK_ORDER[idx] * 60,
            ang_end = -STACK_ORDER[idx+1] * 60
        )
        (dps[idx+1] - dps[idx] > 1 && p == dps[idx+1] - 1) ? (
            ang_start + (ang_end - ang_start) * ease
        ) : (
            ang_start
        )
    ) :
    get_interpolated_ang(dps, p, ease, idx+1);

function get_rev_ang(p, ease) =
    let(
        dps = [for(k = [0 : N_STACK-1]) k + get_rot_count_before(STACK_ORDER, k)]
    )
    (p <= dps[0]) ? -STACK_ORDER[0] * 60 :
    (p >= dps[N_STACK-1]) ? -STACK_ORDER[N_STACK-1] * 60 :
    get_interpolated_ang(dps, p, ease);

// ── 카트리지 회전 각도 (복귀 국면 대칭 보정 적용으로 상승 복귀 시 역순 회전) ──
eff_rev_p = (anim_phase < ANIM_DOWN + ANIM_MID) ? anim_phase : (ANIM_N - 1 - anim_phase);
eff_rev_ease = (anim_phase < ANIM_DOWN + ANIM_MID) ? anim_s : (1 - anim_s);
REV_ANG = get_rev_ang(eff_rev_p, eff_rev_ease);

// ── 수위 (측정 중 수위 변화) ──
WATER_H =
    (_mid_ph >= 0 && _mid_ph < ANIM_MID) ? (
        (_mid_ph == 1) ? 10 * anim_s :
        (_mid_ph == 2) ? 10 + 10 * anim_s :
        (_mid_ph == 3) ? 20 + 10 * anim_s :
        (_mid_ph == 4) ? 30 * (1 - anim_s) : 0
    ) : 0;

// ── 60개 링 동적 상태 추적 ──
// 슬롯 s의 r번째 링이 STACK_ORDER 내에서 매칭되는 인덱스 k를 구함 (없으면 -1)
function find_stack_k(s, r, idx=0, count=0) =
    (idx >= len(STACK_ORDER)) ? -1 :
    (STACK_ORDER[idx] == s) ? (
        (count == r) ? idx : find_stack_k(s, r, idx+1, count+1)
    ) :
    find_stack_k(s, r, idx+1, count);

// 각 슬롯 s에서 현재 페이즈 기준 드롭된 링 개수 구함 (실수형 리턴)
function get_dropped_count(s, p, ease) =
    let(
        // 복귀(상승) 국면 대칭 보정: p가 ANIM_DOWN+ANIM_MID 이상이면 역방향 매핑
        eff_p = (p < ANIM_DOWN + ANIM_MID) ? p : (ANIM_N - 1 - p),
        eff_ease = (p < ANIM_DOWN + ANIM_MID) ? ease : (1 - ease),
        indices = [for(k = [0 : len(STACK_ORDER)-1]) if(STACK_ORDER[k] == s) k]
    )
    len(indices) == 0 ? 0 :
    sum_list([for(k = indices)
        let(dp = k + get_rot_count_before(STACK_ORDER, k))
        (eff_p > dp) ? 1 :
        (eff_p == dp) ? eff_ease :
        0
    ]);

// 링 (s, r)이 현재 페이즈에서 컵 소속인지 여부
function is_ring_in_cup(s, r, phase) =
    let(k = find_stack_k(s, r))
    (k < 0) ? false :
    let(
        dp = k + get_rot_count_before(STACK_ORDER, k),
        up_dp = ANIM_DOWN + ANIM_MID + (ANIM_DOWN - 1 - dp)
    )
    (phase >= dp && phase < up_dp) ? true : false;

// 링 (s, r)의 현재 X, Y 좌표 계산
function get_ring_xy(s, r, phase) =
    is_ring_in_cup(s, r, phase) ? [X_MOVE, 0] :
    let(
        ang = s * 60 + REV_ANG,
        x = REVOLVER_CX + (REVOLVER_PCD/2) * cos(ang),
        y = (REVOLVER_PCD/2) * sin(ang)
    )
    [x, y];

// 링 (s, r)의 현재 Z 좌표 계산
function get_ring_z(s, r, phase, ease) =
    let(k = find_stack_k(s, r))
    (k >= 0 && is_ring_in_cup(s, r, phase)) ? (
        // 컵 내부 적재 위치
        k * RH + Z_MOVE
    ) : (
        // 카트리지 내부 잔류 위치
        let(dc = get_dropped_count(s, phase, ease))
        (r - dc) * RH
    );

// =========================================================================
// [실행부] 메인 시스템 대조립
// =========================================================================
main_system_assembly();

module main_system_assembly() {
    aluminum_profile_frame();
    upper_fixed_base_plate();
    translate([REVOLVER_CX, 0, -10]) teflon_washer_dummy();  // 단 바닥(Z=-10)에 매립 (리볼버축=판중심)
    // ── 벨트 구동 모터 (상판 좌측 전방, 판재 아래 장착) ──
    translate([BELT_MOTOR_X, BELT_MOTOR_Y, 0]) belt_drive_motor_assembly();
    // ── GT2 타이밍 벨트 (모터 풀리 ↔ 중단 허브 벨트 림) ──
    gt2_belt_visual();
    // ── 포토 인터럽터 (원점 복귀 센서) ──
    translate([REVOLVER_CX, 0, 0]) photo_interrupter_assembly();
    // ── 상부 축 지지 브래킷 (보 하면에서 매달림) ──
    translate([REVOLVER_CX, 0, Z_TOP - PF]) upper_shaft_support_bracket();

    // ── 60개 전체 링 물리적 글로벌 렌더링 ──
    // OpenSCAD 투명도 렌더링 순서 상 링(투과 대상)을 투명 파이프/원통보다 먼저 그려야 정상 투과되어 보임
    for(s = [0 : 5]) {
        for(r = [0 : 9]) {
            let(
                xy = get_ring_xy(s, r, anim_phase),
                z = get_ring_z(s, r, anim_phase, anim_s)
            ) {
                translate([xy[0], xy[1], z])
                    color(RING_CLRS[s], 0.9)
                        difference() {
                            cylinder(d=RING_OD, h=RH);
                            translate([0, 0, -0.1]) cylinder(d=RING_IDS[s], h=RH + 0.2);
                        }
            }
        }
    }

    translate([REVOLVER_CX, 0, FLOAT_H]) rotate([0, 0, REV_ANG]) acryl_pipe_revolver_assembly();
    fluidic_control_system_assembly();
    translate([-260, -165, Z_BOT + PF]) water_reservoir_tank();
    
    // 계측 브래킷 모듈 배치
    translate([X_POS_MEASURE, 0, Z_TOP - PF]) acoustic_measurement_module();

    // ---------------------------------------------------------------------
    // 하부 이동 구조체 그룹
    // ---------------------------------------------------------------------
    translate([0, -Y_OFFSET, -252 - 10 - X_RAIL_H/2]) x_stage_rail_dummy();
    translate([0, Y_OFFSET, -252 - 10 - X_RAIL_H/2]) x_stage_rail_dummy();

    translate([X_MOVE, 0, 0]) {
        translate([0, -Y_OFFSET, -252 - 10]) x_slider_block_dummy();
        translate([0, Y_OFFSET, -252 - 10]) x_slider_block_dummy();
        color([0.2, 0.6, 0.3]) translate([0, 0, -252]) h_bridge_adapter_plate();
        
        // OpenSCAD 투명도 렌더링 순서: 컵 내부의 가동부(피스톤, 축)를 먼저 렌더링
        translate([0, 0, Z_MOVE]) z_moving_parts_assembly();
        
        z_cylinder_and_cage();
        // translate([-DRAIN_RADIUS, 0, -CUP_H - CAGE_H + FLOOR_H - BUSHING_H]) bushing_dummy(); // 일체형 가이드홀로 대체되어 제거
        translate([0, 0, -CUP_H - CAGE_H]) color([0.1, 0.1, 0.1]) z_motor_dummy();

        // ── 수위 (개념적 표현) ──
        if (WATER_H > 0.1) color([0.2,0.5,1.0,0.5]) translate([0,0,Z_MOVE])
            cylinder(d=CUP_ID - 2, h=WATER_H);
    }
}

// =========================================================================
// [데이터시트 기반 정밀 재설계] 4인치 Low Frequency Driver 실물 더미
// Mounting: OD=106  PCD=116  Cutout=102  Depth=55mm
// z=0 = 전면 플랜지면 (콘 쪽),  +Z 방향으로 마그넷 연장
// =========================================================================
module speaker_4inch_dummy() {
    OD=106; CUT=102; PCD=116; DEPTH=55; FT=3;  // FT=3 (도면 "3.0")
    CONE_H=22; MAG_D=56; MAG_H=DEPTH-FT-CONE_H;
    FW=120; FCR=10;  // 사각 플랜지 한변 120mm, 코너 R=10mm

    // ── 라운드 사각형 전면 플랜지 (도면 기준) ──
    color([0.13,0.13,0.13]) difference() {
        hull() {
            for(sx=[-1,1]) for(sy=[-1,1])
                translate([sx*(FW/2-FCR), sy*(FW/2-FCR), 0])
                    cylinder(r=FCR, h=FT);
        }
        translate([0,0,-0.1]) cylinder(d=CUT-4, h=FT+0.2);
        // 5.0×6.0 슬롯홀 4개 (PCD 116, 45° 배치)
        for(a=[45,135,225,315]) rotate([0,0,a])
            translate([PCD/2, 0, -0.1]) hull() {
                translate([-0.5, 0, 0]) cylinder(d=5, h=FT+0.2);
                translate([0.5, 0, 0]) cylinder(d=5, h=FT+0.2);
            }
    }

    // ── 바스켓 프레임 (통풍 슬롯 8개) ──
    color([0.11,0.11,0.11]) translate([0,0,FT]) difference() {
        cylinder(d1=OD-4, d2=MAG_D+6, h=CONE_H);
        translate([0,0,-0.1]) cylinder(d1=OD-8, d2=MAG_D+2, h=CONE_H-2);
        for(a=[22.5:45:360]) rotate([0,0,a])
            translate([18,-5,3]) cube([30,10,CONE_H-6]);
    }

    // ── 종이 진동판 콘 ──
    color([0.28,0.25,0.22]) translate([0,0,1]) difference() {
        cylinder(d1=CUT-6, d2=28, h=CONE_H-2);
        translate([0,0,-0.2]) cylinder(d1=CUT-8, d2=26, h=CONE_H-2);
    }

    // ── 더스트 캡 ──
    color([0.15,0.15,0.15]) translate([0,0,CONE_H-3]) difference() {
        scale([1,1,0.4]) sphere(d=30);
        scale([1,1,0.4]) sphere(d=28);
        translate([-20,-20,-20]) cube([40,40,20]);
    }

    // ── 마그넷 어셈블리 (요크 + 자석 + 후면 플레이트) ──
    color([0.18,0.18,0.18]) translate([0,0,FT+CONE_H]) {
        cylinder(d=MAG_D+6, h=3);
        translate([0,0,3]) cylinder(d=MAG_D, h=MAG_H-6);
        translate([0,0,MAG_H-3]) cylinder(d=MAG_D+4, h=3);
    }

    // ── 단자 터미널 ──
    color([0.6,0.6,0.6]) {
        translate([-12,MAG_D/2-3,DEPTH-3]) cube([6,3,3]);
        translate([6,MAG_D/2-3,DEPTH-3]) cube([6,3,3]);
    }
}

// =========================================================================
// [스펙시트 기반 정밀 재설계] Earthworks M50 측정 마이크 실물 더미
// Dimensions: 229 × ø22 mm  |  팁 프로브: ø7 mm
// z=0 = 팁 선단,  +Z 방향으로 본체 (XLR) 연장
// =========================================================================
module m50_mic_dummy() {
    BD=22; TD=7;
    TIP_L=30; TAPER_L=20; BODY_L=155; XLR_L=24;  // 합계 229mm

    color([0.3,0.3,0.3])    translate([0,0,-1])            cylinder(d=TD+0.5, h=1);
    color([0.82,0.82,0.82])                                cylinder(d=TD, h=TIP_L);
    color([0.82,0.82,0.82]) translate([0,0,TIP_L])         cylinder(d1=TD, d2=BD, h=TAPER_L);
    color([0.80,0.80,0.80]) translate([0,0,TIP_L+TAPER_L]) cylinder(d=BD, h=BODY_L);
    color([0.25,0.25,0.25]) translate([0,0,TIP_L+TAPER_L+BODY_L]) cylinder(d=BD, h=XLR_L);
    color([0.15,0.15,0.15]) translate([0,0,229-0.5])
        for(a=[0,120,240]) rotate([0,0,a]) translate([5,0,0]) cylinder(d=2, h=1);
}

// =========================================================================
// [도면 기반 재설계] 음향 계측 통합 브래킷 + 기성품 배치
// 스피커 사각 플랜지(120×120 R=10) 대응, 라운드사각 슈라우드
// 보 하면(z=0) 기준 하향 매달림, 3D 프린팅 단일 파트
// =========================================================================
module acoustic_measurement_module() {
    TOL = 0.3;

    // ── 4인치 스피커 데이터시트 치수 ──
    SPK_OD=106;  SPK_CUT=102;  SPK_PCD=116;
    SPK_DEPTH=55;  SPK_HOLE=5;  SPK_FT=3;

    // ── M50 마이크 ──
    MIC_D=22;  MIC_TD=7;

    // ── 급수관 ──
    TUBE_OD=8;

    // ── 브래킷 설계 파라미터 ──
    WALL = 8;        // 슈라우드 벽 두께 (강화, 날개 직결 구조)

    // ── 스피커 사각 플랜지 치수 ──
    FW=120;  FCR=10;                                  // 사각 플랜지 한변/코너R
    PKT_W = FW + TOL*2;   PKT_CR = FCR + TOL;        // 포켓 120.6×120.6, R=10.3
    SHR_W = PKT_W + WALL*2; SHR_CR = PKT_CR + WALL;  // 슈라우드 136.6×136.6, R=18.3
    SH_EXT = SHR_W / 2;                              // 가이드 앵커용 반폭 (≈68.3)

    // ── 좌표 산출 ──
    SPK_Z  = -SPK_DEPTH;            // -55  (스피커 플랜지 위치, 하면 결합)
    SH_BOT = SPK_Z - WALL;          // -63  (슈라우드 하단)
    SH_H   = -SH_BOT;              // 63   (슈라우드 z=0까지 직접 연장, 상판 판재 대체)

    // ── 마이크 피벗 (슈라우드 하단 — 스피커 간섭 회피) ──
    MP_Z = SH_BOT;                                    // -70

    // ── 마이크 목표: 팁 → 원통 중앙(y=0), 윗면+5mm(z_local=-180) ──
    MIC_ANG  = 35;                                    // 사선 각도 (스피커 우회)
    MIC_PRO  = (MP_Z + 180) / cos(MIC_ANG);           // ≈ 134mm 돌출
    MIC_Y    = -MIC_PRO * sin(MIC_ANG);               // ≈ -77

    // ── 급수관 목표: 팁 → y=35, z_local=-165 ──
    TP_Z = MP_Z;
    TUBE_ANG = atan((65 - 35) / (TP_Z + 165));        // ≈ 17.4°
    TUBE_Y   = 35 + (TP_Z + 165) * tan(TUBE_ANG);     // ≈ 65
    // 노즐 연장: 컵 윗면+30mm(z_local=-155)까지 가이드
    NOZZLE_EXIT_Z = -155;
    NOZZLE_AXIS_L = (TP_Z - NOZZLE_EXIT_Z) / cos(TUBE_ANG);

    // -----------------------------------------------------------------
    // [1] 3D 프린팅 일체형 브래킷 바디
    // -----------------------------------------------------------------
    color([0.25, 0.55, 0.55, 0.85]) difference() {
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

            // ③ 마이크 가이드 브릿지 (슈라우드 벽 → 가이드 출구)
            hull() {
                translate([0, -SH_EXT, MP_Z-15]) cylinder(d=25, h=30);
                translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0])
                    translate([0,0,-20]) cylinder(d=MIC_D+14, h=65);
            }

            // ③-b 마이크 클램프 귀 (가이드 원통 -Y쪽 바깥면, 슬릿 양쪽 ±X)
            translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0]) {
                // 좌우 귀 탭 (원통 바깥면 y=-18에서 10mm 하방 돌출)
                translate([0.75, -(18+10), 5]) cube([10, 10, 25]);
                translate([-(0.75+10), -(18+10), 5]) cube([10, 10, 25]);
            }

            // ④ 급수관 가이드 상부 브릿지 (슈라우드 → 가이드 입구)
            hull() {
                translate([0, SH_EXT, TP_Z-10]) cylinder(d=18, h=20);
                translate([0, TUBE_Y, TP_Z]) rotate([-TUBE_ANG,0,0])
                    translate([0,0,-15]) cylinder(d=TUBE_OD+14, h=55);
            }

            // ⑤ 급수관 연장 노즐 (컵 윗면+3cm까지 사선 가이드)
            translate([0, TUBE_Y, TP_Z]) rotate([-TUBE_ANG,0,0])
                translate([0, 0, -NOZZLE_AXIS_L]) cylinder(d=TUBE_OD+6, h=NOZZLE_AXIS_L-15);
        }

        // ── 감산 가공부 ──

        // ① M5 볼트 관통 (Y방향 보 T슬롯 직결, 날개 관통)
        for(y = [-12, 12]) {
            // X_M 보 (local x = -95, 대칭)
            translate([-95, y, -WALL-1]) cylinder(d=5.5, h=WALL+2);
            translate([-95, y, -WALL-1]) cylinder(d=10, h=4);
            // X_R 보 (local x = +95, 대칭)
            translate([95, y, -WALL-1]) cylinder(d=5.5, h=WALL+2);
            translate([95, y, -WALL-1]) cylinder(d=10, h=4);
        }

        // ② 음파 방사 개구 (하단 벽 관통, d=96 — 플랜지 립 확보)
        translate([0, 0, SH_BOT-1]) cylinder(d=96, h=WALL+1);

        // ③ 스피커 사각 포켓 (하면에서 삽입, 플랜지 레벨~상단)
        translate([0, 0, SPK_Z]) hull() {
            for(sx=[-1,1]) for(sy=[-1,1])
                translate([sx*(PKT_W/2-PKT_CR), sy*(PKT_W/2-PKT_CR), 0])
                    cylinder(r=PKT_CR, h=SPK_DEPTH+5);
        }

        // ④ 스피커 고정 나사 (PCD 116, M5 관통, 4축)
        for(a = [45, 135, 225, 315]) rotate([0,0,a])
            translate([SPK_PCD/2, 0, SH_BOT-1])
                cylinder(d=SPK_HOLE+0.5, h=WALL+SPK_FT+2);

        // ⑤ 배선 관통 (하부, 마그넷 옆)
        translate([0, 0, SPK_Z+SPK_DEPTH-2]) cylinder(d=40, h=WALL+5);

        // ⑥ 마이크 스텝 보어
        translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0]) {
            cylinder(d=MIC_TD+TOL*2, h=500, center=true);
            translate([0,0,-40]) cylinder(d=MIC_D+TOL*2, h=250);
        }

        // ⑥-b 클램프 슬릿 (가이드 원통 전체 높이 절개)
        //    z: -22~+47 (원통 z=-20~+45 전구간 + 여유)
        translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0])
            translate([-0.75, -30, -22]) cube([1.5, 31, 69]);

        // ⑥-c 클램프 볼트홀 (M4, X방향, 귀 중심 관통 — 마이크 바깥쪽)
        translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0])
            translate([0, -23, 17.5]) rotate([0,90,0])
                cylinder(d=4.3, h=40, center=true);

        // ⑦ 급수관 관통 보어
        translate([0, TUBE_Y, TP_Z]) rotate([-TUBE_ANG,0,0])
            cylinder(d=TUBE_OD+TOL, h=500, center=true);

        // ⑧ z≥0 클리핑 (보 영역 침범 방지)
        translate([-115, -120, 0]) cube([230, 240, 80]);
    }

    // -----------------------------------------------------------------
    // [2] 4인치 스피커 실물 더미 배치 (콘 하방)
    // -----------------------------------------------------------------
    translate([0, 0, SPK_Z]) speaker_4inch_dummy();

    // -----------------------------------------------------------------
    // [3] Earthworks M50 마이크 실물 더미 배치
    // -----------------------------------------------------------------
    translate([0, MIC_Y, MP_Z]) rotate([MIC_ANG,0,0])
        translate([0, 0, -MIC_PRO]) m50_mic_dummy();

    // -----------------------------------------------------------------
    // [4] 실리콘 급수 튜브 (노즐 끝+5mm ~ 가이드 상단+10mm)
    // -----------------------------------------------------------------
    TUBE_EXIT = 50;  // 축 z=+40(가이드 상단)+10mm 돌출
    color([0.85, 0.85, 0.85, 0.35])
    translate([0, TUBE_Y, TP_Z]) rotate([-TUBE_ANG,0,0])
        translate([0, 0, -(NOZZLE_AXIS_L+5)]) difference() {
            cylinder(d=TUBE_OD, h=NOZZLE_AXIS_L+5+TUBE_EXIT);
        translate([0,0,-1]) cylinder(d=TUBE_OD-2, h=NOZZLE_AXIS_L+5+TUBE_EXIT+2);
    }
}

// =========================================================================
// [도면 기반 정밀 재설계] X축 모터 일체형 리니어 액추에이터 더미
// 규격: 350mm 스트로크, NEMA 17 (42×42×43), ø8 리드 스크류
// z=0 = 레일 단면 중심,  +X 방향 끝에 모터 장착
// =========================================================================
module x_stage_rail_dummy() {
    SCREW_CZ = 5;          // 리드 스크류 중심 (레일 중심 기준 +5mm)
    MOT_BODY_L = 43;       // NEMA 17 본체 길이
    BRKT_T = 8;            // 엔드 브래킷 두께
    MOTOR_EXTEND = BRKT_T + MOTOR_BOSS_H + MOT_BODY_L + 5;  // 모터 돌출 총 길이 (58mm)
    RAIL_END_X = (X_R + PF) - MOTOR_EXTEND;                   // 모터 끝 = 프레임 바깥면
    RAIL_START_X = RAIL_END_X - X_RAIL_LEN;

    // ── ① 알루미늄 레일 프로파일 본체 (40W × 30H × 350L) ──
    color([0.78, 0.78, 0.78]) difference() {
        translate([RAIL_START_X, -X_RAIL_W/2, -X_RAIL_H/2])
            cube([X_RAIL_LEN, X_RAIL_W, X_RAIL_H]);
        // 상면 V홈 가이드 슬롯
        translate([RAIL_START_X - 1, -10, X_RAIL_H/2 - 4])
            cube([X_RAIL_LEN + 2, 20, 5]);
    }

    // ── ② 리드 스크류 (ø8, 레일 전장) ──
    color([0.60, 0.60, 0.60])
    translate([RAIL_START_X - 3, 0, SCREW_CZ])
        rotate([0, 90, 0]) cylinder(d=SCREW_D, h=X_RAIL_LEN + 6);

    // ── ③ +X 엔드 브래킷 (모터 마운트) ──
    color([0.12, 0.12, 0.12]) difference() {
        translate([RAIL_END_X, -X_RAIL_W/2, -X_RAIL_H/2])
            cube([BRKT_T, X_RAIL_W, X_RAIL_H + 17]);
        translate([RAIL_END_X - 1, 0, SCREW_CZ])
            rotate([0, 90, 0]) cylinder(d=12, h=BRKT_T + 2);
    }

    // ── ④ NEMA 17 스테퍼 모터 (42×42×43mm) ──
    translate([RAIL_END_X + BRKT_T, 0, SCREW_CZ]) {
        // 모터 보스 (ø22 × 2mm)
        color([0.25, 0.25, 0.25])
            rotate([0, 90, 0]) cylinder(d=MOTOR_BOSS_D, h=MOTOR_BOSS_H);
        // 모터 본체
        color([0.15, 0.15, 0.15])
            translate([MOTOR_BOSS_H, -MOTOR_W/2, -MOTOR_W/2])
                cube([MOT_BODY_L, MOTOR_W, MOTOR_W]);
        // 배선 커넥터
        color([0.9, 0.9, 0.9])
            translate([MOTOR_BOSS_H + MOT_BODY_L, -6, -5])
                cube([5, 12, 10]);
    }

    // ── ⑤ 축 커플링 (모터↔스크류, 블루 알루미늄) ──
    color([0.1, 0.45, 0.8])
    translate([RAIL_END_X - 5, 0, SCREW_CZ])
        rotate([0, 90, 0]) cylinder(d=16, h=16);

    // ── ⑥ -X 엔드 브래킷 (베어링 서포트) ──
    color([0.12, 0.12, 0.12]) difference() {
        translate([RAIL_START_X - BRKT_T, -X_RAIL_W/2, -X_RAIL_H/2])
            cube([BRKT_T, X_RAIL_W, X_RAIL_H + 8]);
        translate([RAIL_START_X - BRKT_T - 1, 0, SCREW_CZ])
            rotate([0, 90, 0]) cylinder(d=10, h=BRKT_T + 2);
    }
}

// =========================================================================
// 하단 X축 레일보 고정형 유체 제어 장치 및 순환 배관
// =========================================================================
module fluidic_control_system_assembly() {
    PUMP_X = -120; PUMP_Y = Y_OFFSET; PUMP_Z = Z_RAIL + PF; 
    translate([PUMP_X, PUMP_Y, PUMP_Z]) {
        color([0.2, 0.7, 0.9]) cylinder(d=45, h=30);
        color([0.15, 0.15, 0.15]) translate([-21, -21, 30]) cube([42, 42, 40]); 
        color([0.6, 0.6, 0.6]) { translate([-12, -22, 15]) rotate([90, 0, 0]) cylinder(d=5, h=8); translate([12, -22, 15]) rotate([90, 0, 0]) cylinder(d=5, h=8); }
        color([0.5, 0.5, 0.5]) translate([-25, -20, 0]) { difference() { cube([50, 40, 4]); translate([8, 8, -1]) cylinder(d=4.5, h=6); translate([42, 8, -1]) cylinder(d=4.5, h=6); } }
    }

    VALVE_X = -190; VALVE_Y = Y_OFFSET; VALVE_Z = Z_RAIL - 30; 
    translate([VALVE_X, VALVE_Y, VALVE_Z]) {
        color([0.7, 0.5, 0.2]) cube([30, 40, 30]); 
        color([0.1, 0.1, 0.1]) translate([0, 5, 30]) cube([30, 30, 25]); 
        color([0.6, 0.6, 0.6]) { translate([15, -8, 15]) rotate([90, 0, 0]) cylinder(d=8, h=8); translate([15, 48, 15]) rotate([90, 0, 0]) cylinder(d=8, h=8); }
        color([0.4, 0.4, 0.4]) translate([-5, 5, 25]) cube([40, 30, 5]);
    }

    color([0.9, 0.9, 0.9, 0.5]) { 
        tube_curve([-150, Y_OFFSET + 30, -420], [-150, Y_OFFSET + 30, -310], 8);
        tube_curve([-150, Y_OFFSET + 30, -310], [PUMP_X - 12, PUMP_Y - 22, PUMP_Z + 15], 8);
        // 급수관: 펌프 → 프레임 뒤쪽(Y_B)으로 돌아서 → 브래킷 가이드 상단 출구
        tube_bezier(
            [PUMP_X + 12, PUMP_Y - 22, PUMP_Z + 15],  // P0: 펌프 출구
            [PUMP_X + 12, Y_B + 30, PUMP_Z + 50],      // P1: 뒤쪽으로 올라가는 접선
            [X_POS_MEASURE, Y_B + 30, Z_TOP],           // P2: 브래킷 뒤쪽 상단 접선
            [X_POS_MEASURE, 80, 163],                    // P3: 가이드 상단 +10mm 출구점
            8, 30);
        tube_curve([X_MOVE - DRAIN_RADIUS, 0, Z_MOVE - 260], [(X_MOVE - DRAIN_RADIUS + VALVE_X)/2, 40, -300], 8);
        tube_curve([(X_MOVE - DRAIN_RADIUS + VALVE_X)/2, 40, -300], [VALVE_X + 15, VALVE_Y - 8, VALVE_Z + 15], 8);
        tube_curve([VALVE_X + 15, VALVE_Y + 48, VALVE_Z + 15], [VALVE_X + 15, VALVE_Y + 48, -410], 8);
    }
}

module tube_curve(start, end, d) {
    color([0.9, 0.9, 0.9, 0.3]) hull() {
        translate(start) sphere(d=d);
        translate(end) sphere(d=d);
    }
}

// 3차 베지어 곡선 튜브 (4개 제어점, N 세그먼트)
module tube_bezier(P0, P1, P2, P3, d, N=20) {
    color([0.9, 0.9, 0.9, 0.3])
    for(i = [0 : N-1]) {
        t0 = i / N;
        t1 = (i + 1) / N;
        // 드 카스텔자우 3차 베지어
        a0 = (1-t0)*(1-t0)*(1-t0);
        b0 = 3*(1-t0)*(1-t0)*t0;
        c0 = 3*(1-t0)*t0*t0;
        d0 = t0*t0*t0;
        a1 = (1-t1)*(1-t1)*(1-t1);
        b1 = 3*(1-t1)*(1-t1)*t1;
        c1 = 3*(1-t1)*t1*t1;
        d1 = t1*t1*t1;
        pt0 = [a0*P0[0]+b0*P1[0]+c0*P2[0]+d0*P3[0],
               a0*P0[1]+b0*P1[1]+c0*P2[1]+d0*P3[1],
               a0*P0[2]+b0*P1[2]+c0*P2[2]+d0*P3[2]];
        pt1 = [a1*P0[0]+b1*P1[0]+c1*P2[0]+d1*P3[0],
               a1*P0[1]+b1*P1[1]+c1*P2[1]+d1*P3[1],
               a1*P0[2]+b1*P1[2]+c1*P2[2]+d1*P3[2]];
        hull() {
            translate(pt0) sphere(d=d);
            translate(pt1) sphere(d=d);
        }
    }
}

// =========================================================================
// 3030 알루미늄 프로파일 전체 골조 프레임 모듈
// =========================================================================
module aluminum_profile_frame() { 
    color([0.75, 0.75, 0.75]) { 
        translate([X_L, Y_B, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); translate([X_L, Y_F, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); 
        translate([X_M, Y_B, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); translate([X_M, Y_F, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); 
        translate([X_R, Y_B, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); translate([X_R, Y_F, Z_BOT]) cube([PF, PF, Z_TOP - Z_BOT]); 
    } 
    color([0.65, 0.65, 0.65]) { 
        translate([X_L + PF, Y_B, Z_BOT]) cube([X_R - X_L - PF, PF, PF]); translate([X_L + PF, Y_F, Z_BOT]) cube([X_R - X_L - PF, PF, PF]); 
        translate([X_L, Y_F + PF, Z_BOT]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_R, Y_F + PF, Z_BOT]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_M, Y_F + PF, Z_BOT]) cube([PF, Y_B - Y_F - PF, PF]); 
    } 
    color([0.8, 0.8, 0.8]) { 
        translate([X_L, -Y_OFFSET - PF/2, Z_RAIL]) cube([X_R - X_L + PF, PF, PF]); translate([X_L, Y_OFFSET - PF/2, Z_RAIL]) cube([X_R - X_L + PF, PF, PF]); 
        translate([X_L, Y_F + PF, Z_RAIL]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_R, Y_F + PF, Z_RAIL]) cube([PF, Y_B - Y_F - PF, PF]); // X_M 크로스빔 제거 (Z축 스크류 이동 간섭 방지)
    } 
    color([0.7, 0.7, 0.7]) { 
        translate([X_L + PF, Y_B, Z_MID]) cube([X_M - X_L - PF, PF, PF]); translate([X_L + PF, Y_F, Z_MID]) cube([X_M - X_L - PF, PF, PF]); 
        translate([X_L, Y_F + PF, Z_MID]) cube([PF, Y_B - Y_F - PF, PF]); translate([-95, Y_F + PF, Z_MID]) cube([PF, Y_B - Y_F - PF, PF]); 
    } 
    color([0.75, 0.75, 0.75]) { 
        translate([X_L + PF, Y_B, Z_TOP - PF]) cube([X_R - X_L - PF, PF, PF]); translate([X_L + PF, Y_F, Z_TOP - PF]) cube([X_R - X_L - PF, PF, PF]); 
        translate([X_L, Y_F + PF, Z_TOP - PF]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_M, Y_F + PF, Z_TOP - PF]) cube([PF, Y_B - Y_F - PF, PF]); translate([X_R, Y_F + PF, Z_TOP - PF]) cube([PF, Y_B - Y_F - PF, PF]); 
    } 
    color([0.65, 0.65, 0.65]) { 
        translate([X_L + PF, -PF/2, Z_TOP - PF]) cube([X_M - X_L - PF, PF, PF]); // 리볼버 축 중심 단일 보 (Y=0 정렬)
    } 
    // 측정 브래킷 장착용 가로보 (X방향, Y=0 중심, 프레임 강성 보강)
    color([0.75, 0.75, 0.75]) { 
        translate([X_M + PF, -PF/2, Z_TOP - PF]) cube([X_R - X_M - PF, PF, PF]); 
    } 
}

// =========================================================================
// [GT2 타이밍 벨트 구동] 벨트 모터 어셈블리
// NEMA 17 스테퍼를 상판 위 브래킷에 장착, 축 상향 → 풀리 구동
// 원점 = 모터 축 중심, z=0 = 상판 윗면
// =========================================================================
module belt_drive_motor_assembly() {
    MOT_BODY_L = 43;            // NEMA 17 본체 길이
    SHAFT_L = 24;               // 축 돌출 길이
    PULLEY_Z = MID_HUB_Z + (HUB_H - GT2_BELT_W) / 2 + (BOSS_H + WASHER_T - 10) - 1;  // 풀리 하면 Z (허브 중심 벨트 정렬, -1=플랜지)

    // ── ① 모터 브래킷 (상판 위, 모터영역+연장부) ──
    // 모터 좌측: 모터 볼팅 (31mm 피치, 고정)
    // 우측 연장: 상판 슬롯볼트 (X방향 장력 조절)
    BRKT_EXT = 30;  // 우측 연장 길이
    BRKT_TOTAL_X = BRKT_MOTOR_W + BRKT_EXT;  // 총 X길이 = 80mm
    color([1.0, 0.5, 0.0]) difference() {
        // 블록 본체 (모터 중심 기준, 좌측 -25, 우측 +55)
        translate([-BRKT_MOTOR_W/2, -BRKT_MOTOR_W/2, 0])
            cube([BRKT_TOTAL_X, BRKT_MOTOR_W, BRKT_MOTOR_H]);
        // NEMA 17 마운트홀 (31mm 피치, 고정) + 하면 카운터보어
        for(dx = [-MOTOR_PITCH/2, MOTOR_PITCH/2])
            for(dy = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
                translate([dx, dy, -1]) cylinder(d=MOTOR_HOLE_D, h=BRKT_MOTOR_H+2);  // 관통홀
                translate([dx, dy, -1]) cylinder(d=MOTOR_CB_D, h=MOTOR_CB_DEPTH+1);  // 카운터보어 깊이19 (M3×10 단볼트)
            }
        // 중앙 관통홀 (모터 보스 클리어런스)
        translate([0, 0, -1]) cylinder(d=MOTOR_BOSS_D + 1, h=BRKT_MOTOR_H+2);
        // 상판 체결 슬롯 (우측 연장부, X방향 슬롯 → 장력 조절) — Y피치 25 공유
        for(dy = [-MOTOR_BOLT_PITCH/2, MOTOR_BOLT_PITCH/2])
            hull() {
                translate([BRKT_MOTOR_W/2 + 8, dy, -1]) cylinder(d=4.5, h=BRKT_MOTOR_H+2);
                translate([BRKT_MOTOR_W/2 + 8 + SLOT_LEN, dy, -1]) cylinder(d=4.5, h=BRKT_MOTOR_H+2);
            }
    }

    // ── ② NEMA 17 모터 본체 (브래킷 위, 축 상향) ──
    color([0.1, 0.1, 0.1])
        translate([-MOTOR_W/2, -MOTOR_W/2, BRKT_MOTOR_H])
            cube([MOTOR_W, MOTOR_W, MOT_BODY_L]);

    // ── ③ 모터 보스 (ø22 × 2mm, 상면) ──
    color([0.25, 0.25, 0.25])
        translate([0, 0, BRKT_MOTOR_H + MOT_BODY_L])
            cylinder(d=MOTOR_BOSS_D, h=MOTOR_BOSS_H);

    // ── ④ 모터 축 (상면에서 위로 돌출) ──
    color([0.7, 0.7, 0.7])
        translate([0, 0, BRKT_MOTOR_H + MOT_BODY_L])
            cylinder(d=5, h=SHAFT_L);

    // ── ⑤ GT2 20치 풀리 (중단 허브 벨트 높이 맞춤) ──
    color([0.8, 0.75, 0.1]) translate([0, 0, PULLEY_Z]) difference() {
        union() {
            cylinder(d=SMALL_PULLEY_OD, h=GT2_BELT_W + 2);
            cylinder(d=SMALL_PULLEY_OD + 4, h=1);               // 하부 플랜지
            translate([0, 0, GT2_BELT_W + 1])
                cylinder(d=SMALL_PULLEY_OD + 4, h=1);           // 상부 플랜지
        }
        translate([0, 0, -1]) cylinder(d=5.2, h=GT2_BELT_W + 4);
    }

    // ── ⑥ 배선 커넥터 (모터 하면, 브래킷 안쪽) ──
    color([0.9, 0.9, 0.9])
        translate([-6, -5, BRKT_MOTOR_H - 3])
            cube([12, 10, 3]);
}

// [원점 센서] 투과형 포토 인터럽터 + L브래킷
// 하단 허브 외주의 플래그를 감지하여 원점(0°) 확인
// 센서 ㄷ자 슬롯이 플래그 회전 경로를 상하로 감싸고,
// 플래그가 접선 방향으로 슬롯을 통과하여 빛을 차단
// 원점 = 리볼버 중심, z=0 = 상판 윗면
// =========================================================================
module photo_interrupter_assembly() {
    // 플래그 회전 경로의 중심 반경 (허브 외경 + 5mm)
    FLAG_R = CARTRIDGE_OD/2 + 5;  // = 172mm (허브 167mm 바깥)

    ARM_T = 3;                         // ㄷ 팔 두께 (Z)
    SLOT_H = FLAG_H + 2;              // 슬롯 높이 = 10mm (플래그 8mm + 여유 2mm)
    SENS_W = 10;                       // 센서 폭 (X, 접선방향)
    SENS_D = 8;                        // 센서 깊이 (Y, 반경방향, 팔 길이)

    translate([0, -FLAG_R, 0]) {
        // ── 투과형 포토 인터럽터 (ㄷ자, 상판 직접 볼팅) ──
        color([0.1, 0.1, 0.1]) difference() {
            translate([-SENS_W/2, -SENS_D/2, 0]) union() {
                // 하부 팔 (상판 위에 직접 안착)
                cube([SENS_W, SENS_D, ARM_T]);
                // 배면 벽 (바깥쪽, 상하 팔 연결)
                cube([SENS_W, ARM_T, ARM_T * 2 + SLOT_H]);
                // 상부 팔
                translate([0, 0, ARM_T + SLOT_H])
                    cube([SENS_W, SENS_D, ARM_T]);
            }
            // 상판 체결 볼트홀 (하부 팔 관통)
            for(dx = [-3, 3])
                translate([dx, 0, -1]) cylinder(d=2.5, h=ARM_T + 2);
        }
        // ── PCB 보드 (센서 뒤쪽, 수직 세움, YwRobot 스타일) ──
        color([0.05, 0.1, 0.25]) translate([-0.8, -SENS_D/2 - 35, 0])
            difference() {
                cube([1.6, 35, 12]);  // 1.6T × 35mm × 12mm 수직 보드
                translate([-0.5, 4, 6]) rotate([0, 90, 0]) cylinder(d=3, h=2.6);
                translate([-0.5, 30, 6]) rotate([0, 90, 0]) cylinder(d=3, h=2.6);
            }
    }
}

// =========================================================================
// [상부 축 지지] ㅛ자 안장형 브래킷
// 두 탭이 보 양쪽면으로 올라가서 수평 볼트로 T슬롯 체결
// 아래로 벌어지며 내려와 하단판에서 보스 관통홀(ø36) 확보
// 원점 = 리볼버 축 중심, z=0 = 보 하면 (Z_TOP - PF)
// =========================================================================
module upper_shaft_support_bracket() {
    BRKT_T = 8.0;              // 측벽/탭/연결판 두께 (PLA 강성 확보)
    BOTTOM_T = 10.0;           // 바닥판 두께 (보스 베어링 지지)
    FLOAT_H = BOSS_H + WASHER_T - 10;  // 리볼버 Z 오프셋 = 2mm
    UPPER_GAP = 2.0;           // 상단 허브 상면↔바닥판 하면 간격
    DROP_H = (Z_TOP - PF) - (FLOAT_H + UPPER_HUB_Z + HUB_H + UPPER_GAP + BOTTOM_T);  // 보 하면→바닥판 상면
    BOSS_CLEAR = BOSS_OD + 1.0;  // 36mm
    PLATE_W = 50.0;            // X방향 폭
    HALF_BEAM = PF / 2;        // 보 반폭 = 10mm
    HALF_GAP = BOSS_CLEAR/2 + 5;  // 하부 벽 반간격 = 23mm

    color([0.55, 0.3, 0.6, 0.85]) difference() {
        union() {
            // ── ㅛ 상부: 좌측 탭 (보 -Y면을 따라 위로) ──
            translate([-PLATE_W/2, -HALF_BEAM - BRKT_T, 0])
                cube([PLATE_W, BRKT_T, PF]);
            // ── ㅛ 상부: 우측 탭 (보 +Y면을 따라 위로) ──
            translate([-PLATE_W/2, HALF_BEAM, 0])
                cube([PLATE_W, BRKT_T, PF]);
            // ── ㅛ 연결: 좌측 수평 연결판 (탭→벽) ──
            translate([-PLATE_W/2, -HALF_GAP - BRKT_T, -BRKT_T])
                cube([PLATE_W, HALF_GAP + BRKT_T - HALF_BEAM, BRKT_T]);
            // ── ㅛ 연결: 우측 수평 연결판 ──
            translate([-PLATE_W/2, HALF_BEAM, -BRKT_T])
                cube([PLATE_W, HALF_GAP + BRKT_T - HALF_BEAM, BRKT_T]);
            // ── ㅛ 하부: 좌측 벽 ──
            translate([-PLATE_W/2, -HALF_GAP - BRKT_T, -DROP_H])
                cube([PLATE_W, BRKT_T, DROP_H - BRKT_T]);
            // ── ㅛ 하부: 우측 벽 ──
            translate([-PLATE_W/2, HALF_GAP, -DROP_H])
                cube([PLATE_W, BRKT_T, DROP_H - BRKT_T]);
            // ── ㅛ 하부: 바닥판 (보스 상단에서 아래로 10mm) ──
            translate([-PLATE_W/2, -HALF_GAP - BRKT_T, -DROP_H - BOTTOM_T])
                cube([PLATE_W, (HALF_GAP + BRKT_T) * 2, BOTTOM_T]);
        }
        // ── 보스 관통홀 (바닥판 관통) ──
        translate([0, 0, -DROP_H - BOTTOM_T - 1]) cylinder(d=BOSS_CLEAR, h=BOTTOM_T + 2);
        // ── 좌측 보 체결 볼트 (수평, +Y → 보 측면 T슬롯) ──
        for(dx = [-15, 15])
            translate([dx, -HALF_BEAM - BRKT_T - 1, PF/2])
                rotate([-90, 0, 0]) cylinder(d=4.5, h=BRKT_T + 2);
        // ── 우측 보 체결 볼트 (수평, -Y → 보 측면 T슬롯) ──
        for(dx = [-15, 15])
            translate([dx, HALF_BEAM - 1, PF/2])
                rotate([-90, 0, 0]) cylinder(d=4.5, h=BRKT_T + 2);
    }
}

// =========================================================================
// 하부 고정 서브 시스템 하우징 모듈 그룹
// =========================================================================
module upper_fixed_base_plate() { color([0.5, 0.5, 0.5, 0.5]) { difference() { translate([X_L, Y_F, -TOP_PLATE_H]) cube([(X_M + PF) - X_L, (Y_B + PF) - Y_F, TOP_PLATE_H]); translate([X_L - 1, Y_B - 1, -TOP_PLATE_H - 1]) cube([PF + 1, PF + 1, TOP_PLATE_H + 2]); translate([X_L - 1, Y_F - 1, -TOP_PLATE_H - 1]) cube([PF + 1, PF + 1, TOP_PLATE_H + 2]); translate([X_M, Y_B - 1, -TOP_PLATE_H - 1]) cube([PF + 1, PF + 1, TOP_PLATE_H + 2]); translate([X_M, Y_F - 1, -TOP_PLATE_H - 1]) cube([PF + 1, PF + 1, TOP_PLATE_H + 2]); translate([DROP_X, -(CUP_OD + 1)/2, -TOP_PLATE_H - 1]) cube([CARTRIDGE_OD, CUP_OD + 1, TOP_PLATE_H + 2]); translate([DROP_X, 0, -TOP_PLATE_H - 1]) cylinder(d=CUP_OD + 1, h=TOP_PLATE_H + 2); translate([REVOLVER_CX, 0, -10.1]) cylinder(d=36, h=10.2); /* 10mm 블라인드홀 (하층 5T 막힘) - 하단 보스 수용 */ for(hx = [MOTOR_BOLT_X_NOMINAL, MOTOR_BOLT_X_SHIFT]) for(hy = [BELT_MOTOR_Y - MOTOR_BOLT_PITCH/2, BELT_MOTOR_Y + MOTOR_BOLT_PITCH/2]) translate([hx, hy, -TOP_PLATE_H - 1]) cylinder(d=4.5, h=TOP_PLATE_H + 2); /* 모터 체결홀 X2열(55,40)×Y피치25 */ } } }

module acryl_pipe_revolver_assembly() {
    PIPE_H = UPPER_HUB_Z + POCKET_DEPTH - (HUB_H - POCKET_DEPTH);  // 파이프 전체 높이
    SQ = SHAFT_SQ + GLOBAL_TOLERANCE;  // 20.2mm 사각 홀 (프레임 PF와 독립)

    // ── 2020 회전축 (하단 보스 하면 ~ 상단 보스 상면) ──
    color([0.6, 0.6, 0.6])
        translate([-SHAFT_SQ/2, -SHAFT_SQ/2, -BOSS_H])
            cube([SHAFT_SQ, SHAFT_SQ, BOSS_H + UPPER_HUB_Z + HUB_H + BOSS_H]);

    // ========== 하단 허브 (Z=0 ~ HUB_H, 검은 아크릴 10T) ==========
    color([0.1, 0.1, 0.1]) translate([0, 0, 0]) difference() {
        union() {
            cylinder(d=CARTRIDGE_OD, h=HUB_H);                    // 메인 디스크
            translate([0, 0, -BOSS_H]) cylinder(d=BOSS_OD, h=BOSS_H);  // 하부 보스
        }
        // 사각 축 소켓 (상면에서 5mm 삽입, 하면은 솔리드)
        translate([-SQ/2, -SQ/2, HUB_H - POCKET_DEPTH]) cube([SQ, SQ, POCKET_DEPTH + 1]);
        // 6× 파이프 소켓 (상면에서 POCKET_DEPTH 삽입, 파이프가 위에서 꽂힘)
        for(a = [0 : 60 : 359]) rotate([0, 0, a])
            translate([REVOLVER_PCD/2, 0, HUB_H - POCKET_DEPTH])
                cylinder(d=ACRYL_OD + GLOBAL_TOLERANCE, h=POCKET_DEPTH + 1);
        // 6× 지컵 관통 (컵 ID, 링 낙하용)
        for(a = [0 : 60 : 359]) rotate([0, 0, a])
            translate([REVOLVER_PCD/2, 0, -1])
                cylinder(d=CUP_ID + 0.5, h=HUB_H + 2);
        // 6× 지컵 하면 모따기 C2 (디스크 하면 Z=0, 링 낙하 가이드)
        for(a = [0 : 60 : 359]) rotate([0, 0, a])
            translate([REVOLVER_PCD/2, 0, -0.1])
                cylinder(d1=CUP_ID + 0.5 + 4, d2=CUP_ID + 0.5, h=2.1);
    }

    // ========== 중단 허브 (Z=MID_HUB_Z, 검은 아크릴, 벨트 림) ==========
    color([0.1, 0.1, 0.1]) translate([0, 0, MID_HUB_Z]) difference() {
        union() {
            cylinder(d=CARTRIDGE_OD, h=HUB_H);                    // 메인 디스크
            // 벨트 외주 림
            difference() {
                cylinder(d=BIG_PULLEY_OD, h=HUB_H);
                translate([0, 0, -1]) cylinder(d=BIG_PULLEY_OD - 14, h=HUB_H + 2);
            }
        }
        // 사각 축 관통
        translate([-SQ/2, -SQ/2, -1]) cube([SQ, SQ, HUB_H + 2]);
        // 6× 파이프 관통홀 (중단은 삽입이 아닌 통과)
        for(a = [0 : 60 : 359]) rotate([0, 0, a])
            translate([REVOLVER_PCD/2, 0, -1])
                cylinder(d=ACRYL_OD + GLOBAL_TOLERANCE, h=HUB_H + 2);
    }
    // 중단 축 클램프 보스 (별도 부품, 3D 프린팅)
    color([1.0, 0.5, 0.0]) translate([0, 0, MID_HUB_Z - 20]) difference() {
        translate([-15, -15, 0]) cube([30, 30, 20]);  // 30×30×20mm (허브 하면까지)
        // 사각 축 관통
        translate([-SQ/2, -SQ/2, -1]) cube([SQ, SQ, 22]);
        // M4 관통홀 4방향
        for(ang = [0, 90, 180, 270])
            rotate([0, 0, ang]) translate([0, 0, 10])
                rotate([0, 90, 0]) translate([0, 0, SQ/2 - 1])
                    cylinder(d=4.5, h=16);
    }
    // 포토 인터럽터 플래그 (하단 허브 외주, 센서 위치에 정렬)
    // REV_ANG 상쇄: 리볼버 전체가 REV_ANG만큼 회전하므로 -90-REV_ANG으로 보정
    rotate([0, 0, -90 - REV_ANG]) color([0.1, 0.1, 0.1])
        translate([CARTRIDGE_OD/2 - 0.5, -2.5, 4])
            cube([5, 5, HUB_H - 4]);  // Z=4~HUB_H, 하단 허브 윗면에 맞춤
    // 뒤집힌 GT2 벨트 (중단 허브 외주 부착, 치면 외향)
    color([0.15, 0.15, 0.15]) translate([0, 0, MID_HUB_Z + (HUB_H - GT2_BELT_W) / 2])
        difference() {
            cylinder(d=BIG_PULLEY_OD + 3, h=GT2_BELT_W);
            translate([0, 0, -1]) cylinder(d=BIG_PULLEY_OD - 0.5, h=GT2_BELT_W + 2);
        }

    // ========== 상단 허브 (Z=UPPER_HUB_Z, 검은 아크릴, 상부 보스 + 하부 파이프 소켓) ==========
    color([0.1, 0.1, 0.1]) translate([0, 0, UPPER_HUB_Z]) difference() {
        union() {
            cylinder(d=CARTRIDGE_OD, h=HUB_H);                    // 메인 디스크
            translate([0, 0, HUB_H]) cylinder(d=BOSS_OD, h=BOSS_H);  // 상부 보스 (축 브래킷 지지)
        }
        // 사각 축 관통
        translate([-SQ/2, -SQ/2, -1]) cube([SQ, SQ, HUB_H + BOSS_H + 2]);
        // 6× 파이프 소켓 (하면에서 POCKET_DEPTH 삽입 → 파이프에 얹힘)
        for(a = [0 : 60 : 359]) rotate([0, 0, a])
            translate([REVOLVER_PCD/2, 0, -1])
                cylinder(d=ACRYL_OD + GLOBAL_TOLERANCE, h=POCKET_DEPTH + 1);
        // 6× 지컵 관통 (컵 ID)
        for(a = [0 : 60 : 359]) rotate([0, 0, a])
            translate([REVOLVER_PCD/2, 0, -1])
                cylinder(d=CUP_ID + 0.5, h=HUB_H + BOSS_H + 2);
    }
    // 상단 축 클램프 보스 (별도 부품, 3D 프린팅)
    color([1.0, 0.5, 0.0]) translate([0, 0, UPPER_HUB_Z - 20]) difference() {
        translate([-15, -15, 0]) cube([30, 30, 20]);  // 30×30×20mm (허브 하면까지)
        // 사각 축 관통
        translate([-SQ/2, -SQ/2, -1]) cube([SQ, SQ, 22]);
        // M4 관통홀 4방향
        for(ang = [0, 90, 180, 270])
            rotate([0, 0, ang]) translate([0, 0, 10])
                rotate([0, 90, 0]) translate([0, 0, SQ/2 - 1])
                    cylinder(d=4.5, h=16);
    }

    // ========== 아크릴 파이프 + 링 ==========
    for(a = [0 : 60 : 359]) {
        rotate([0, 0, a]) translate([REVOLVER_PCD/2, 0, HUB_H - POCKET_DEPTH]) {
            color([0.1, 0.7, 0.9, 0.30]) difference() {
                cylinder(d=ACRYL_OD, h=PIPE_H);
                translate([0, 0, -1]) cylinder(d=ACRYL_ID, h=PIPE_H + 2);
            }
        }
    }

}
module h_bridge_adapter_plate() { difference() { hull() { translate([0, -Y_OFFSET, 0]) cylinder(d = X_BLOCK_L + 10, h = BRKT_H); translate([0, 0, 0]) cylinder(d = BRKT_D, h = BRKT_H); translate([0, Y_OFFSET, 0]) cylinder(d = X_BLOCK_L + 10, h = BRKT_H); } translate([0, -Y_OFFSET, 0]) { for(x = [-X_PITCH_X/2, X_PITCH_X/2]) { for(y = [-X_PITCH_Y/2, X_PITCH_Y/2]) { translate([x, y, -1]) cylinder(d = 4.5, h = BRKT_H + 2); } } } translate([0, Y_OFFSET, 0]) { for(x = [-X_PITCH_X/2, X_PITCH_X/2]) { for(y = [-X_PITCH_Y/2, X_PITCH_Y/2]) { translate([x, y, -1]) cylinder(d = 4.5, h = BRKT_H + 2); } } } translate([0, 0, -1]) cylinder(d = BRKT_ID, h = BRKT_H + 2); for(a = [45, 135, 225, 315]) { rotate([0, 0, a]) translate([Z_MOUNT_PCD/2, 0, -1]) cylinder(d = 4.5, h = BRKT_H + 2); } translate([-DRAIN_RADIUS, 0, -1]) cylinder(d = 14, h = BRKT_H + 2); } }
module z_cylinder_and_cage() {
    // ── 아크릴 파이프 소켓 파라미터 ──
    SOCK_ID = ACRYL_OD + GLOBAL_TOLERANCE;  // 106.2mm (아크릴 OD106 수용)
    SOCK_WALL = 5;                           // 소켓 벽 두께
    SOCK_OD = SOCK_ID + SOCK_WALL * 2;       // 116.2mm
    SOCK_H = 15;                             // 소켓 높이 (끼움 깊이)

    // ── ③ 케이지 (모터 마운트+드레인+컵 소켓 턱 통합) ──
    CUP_SOCK_H = 15;  // 컵 외벽 감싸는 소켓 턱 높이
    color([0.85, 0.85, 0.85, 1.0]) {
        union() {
            difference() {
                // 케이지 본체 + 소켓 턱 (Z=-240 ~ Z=-165)
                translate([0, 0, -CUP_H - CAGE_H]) cylinder(d=SOCK_OD, h=CAGE_H + CUP_SOCK_H);
                // 내부 공간 (CUP_ID=100, 피스톤 영역)
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H]) cylinder(d=CUP_ID, h=CAGE_H - FLOOR_H + 0.1);
                // 소켓 턱 내경 (CUP_OD+공차=110.2, 컵 외벽 수용)
                translate([0, 0, -CUP_H]) cylinder(d=CUP_OD + GLOBAL_TOLERANCE, h=CUP_SOCK_H + 0.1);
                // 측면 개구부 (경량화/접근)
                translate([-32.5, -SOCK_OD/2 - 10, -CUP_H - CAGE_H + FLOOR_H + 5]) cube([65, SOCK_OD + 20, CAGE_H - FLOOR_H - 10]);
                translate([0, 0, -CUP_H - CAGE_H - 0.1]) cylinder(d = MOTOR_BOSS_D + GLOBAL_TOLERANCE, h = FLOOR_H + 0.2);
                translate([0, 0, -CUP_H - CAGE_H - 1]) {
                    for(x = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
                        for(y = [-MOTOR_PITCH/2, MOTOR_PITCH/2]) {
                            translate([x, y, 0]) cylinder(d = MOTOR_HOLE_D, h = FLOOR_H + 3);
                        }
                    }
                }
                translate([0, 0, -CUP_H - CAGE_H - 1]) {
                    for(a = [45, 135, 225, 315]) {
                        rotate([0, 0, a]) translate([Z_MOUNT_PCD/2, 0, 0]) cylinder(d = 4.5, h = FLOOR_H + 2);
                    }
                }
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H + LEAK_DRAIN_D/2]) rotate([0, -90, 0]) cylinder(d = LEAK_DRAIN_D, h = SOCK_OD/2 + 10);
                // 일체형 가이드 부싱 홀 (외경 ø8.0 파이프 가이드용 슬라이딩 공차 적용 ø8.3 관통)
                translate([-DRAIN_RADIUS, 0, -CUP_H - CAGE_H - 1]) cylinder(d = GUIDE_PIPE_D + 0.3, h = FLOOR_H + 2);
            }
            difference() {
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H]) cylinder(d=LIP_D, h=LIP_H);
                translate([0, 0, -CUP_H - CAGE_H + FLOOR_H - 0.1]) cylinder(d = MOTOR_BOSS_D + GLOBAL_TOLERANCE, h = LIP_H + 0.2);
            }
        }
    }

    // ── ① 아크릴 원통 (컵, OD110/ID100) ──
    // OpenSCAD 투명도 렌더링 순서 상 불투명한 하부 케이지를 먼저 렌더링한 후 투명 아크릴을 나중에 렌더링
    color([0.2, 0.5, 0.8, 0.30]) {
        difference() {
            translate([0, 0, -CUP_H]) cylinder(d=CUP_OD, h=CUP_H);
            translate([0, 0, -CUP_H - 0.1]) cylinder(d=CUP_ID, h=CUP_H + 0.2);
        }
    }
}
// ── T8 암나사산 생성 모듈 (외경 ø8.25, 이빨끝 R3.35) ──
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
        // 플랜지 테두리 손가락 홈 12개 (반경 방향 2mm 깊게 파냄)
        for (a = [0:30:359]) rotate([0, 0, a])
            translate([FLANGE_D/2 + 0.5, 0, -1]) cylinder(d = 7, h = FLANGE_T + 2, $fn = 30);
    }
}

module z_moving_parts_assembly() {
    ORING_W = 4.8; ORING_GROOVE_D = 93.0; ORING_Z = 10.0;

    color([1.0, 0.5, 0.0, 1.0]) difference() {
        union() {
            // 피스톤 본체 (외경 ø98.8mm로 확장하여 유격 최적화)
            translate([0, 0, -PISTON_H]) cylinder(d=98.8, h=PISTON_H);
            // 배수구 하부 가이드 보스 (Boss)
            translate([-DRAIN_RADIUS, 0, -PISTON_H - 10]) cylinder(d=15, h=10);
        }
        // 3D 프린팅 일체형 T8 나사산 (상면 Z=0 에서 5mm 남기고 진입)
        translate([0, 0, -PISTON_H - 0.1])
            t8_internal_thread_subtraction(PISTON_H - 5 + 0.1);
            
        // 배수관 단턱 소켓 (Z=-5 ~ 0 은 ø6.0 관통, Z=-30 ~ -5 은 ø8.2 소켓)
        translate([-DRAIN_RADIUS, 0, -5]) cylinder(d=6.0, h=6.1);
        translate([-DRAIN_RADIUS, 0, -PISTON_H - 10 - 1]) cylinder(d=DRAIN_D + GLOBAL_TOLERANCE, h=PISTON_H + 10 - 5 + 1.1);
        
        // 오링 홈 (외주면 1줄, 홈 바닥 ø93.0mm, 홈 폭 4.8mm)
        translate([0, 0, -ORING_Z - ORING_W/2]) difference() {
            cylinder(d = CUP_ID + 2, h = ORING_W);
            translate([0, 0, -0.5]) cylinder(d = ORING_GROOVE_D, h = ORING_W + 1);
        }
        
        // ── 피스톤 상면 배수 유로 홈 (Water Channel) ──
        // 음향 공명에 방해를 주지 않도록 중앙에서 7mm 떨어진 위치부터 배수구(X=-35) 방향으로 향하는 1줄의 홈만 형성 (폭 4mm, 깊이 3mm)
        rotate([0, 0, 180]) translate([7, -2, -3]) cube([DRAIN_RADIUS - 7 + 2, 4, 3.1]);
    }
    // T8 잼 플랜지 너트 (피스톤 하단 Z=-PISTON_H 밀착 체결 및 T8 스크류 이중 고정)
    translate([0, 0, -PISTON_H]) rotate([180, 0, 0]) color([0.9, 0.45, 0.1]) t8_flange_nut();

    // T8 리드스크류 (Z=-5에서 시작하여 280mm 하방 연장)
    translate([0, 0, -5]) rotate([180, 0, 0]) color([0.9, 0.9, 0.2]) cylinder(d=8, h=280);
    // 알루미늄 튜브 (ø8 × 1.0T, Z=-5에서 시작하여 250mm 하방 연장)
    translate([-DRAIN_RADIUS, 0, -5]) rotate([180, 0, 0]) color([0.55, 0.57, 0.6, 1.0]) difference() {
        cylinder(d=GUIDE_PIPE_D, h=250);
        translate([0,0,-1]) cylinder(d=GUIDE_PIPE_D - 2.0, h=252);
    }
    // 오링 실링 (검은색 NBR/실리콘 고무, 피스톤 홈에 장착됨)
    translate([0, 0, -ORING_Z]) color([0.15, 0.15, 0.15, 1.0]) {
        rotate_extrude($fn = 80) {
            translate([(ORING_GROOVE_D + CUP_ID) / 4, 0, 0])
                circle(d = ORING_W, $fn = 30);
        }
    }
}
module z_motor_dummy() { difference() { union() { translate([-MOTOR_W/2, -MOTOR_W/2, -40]) cube([MOTOR_W, MOTOR_W, 40]); cylinder(d=MOTOR_BOSS_D, h=MOTOR_BOSS_H); } translate([0, 0, -45]) cylinder(d = SCREW_D + 2, h = 50); } }
module bushing_dummy() { color([0.8, 0.55, 0.3, 1.0]) difference() { cylinder(d = BUSHING_OD, h = BUSHING_H); translate([0, 0, -1]) cylinder(d = GUIDE_PIPE_D, h = BUSHING_H + 2); } }
module x_slider_block_dummy() {
    // ── ① 캐리지 상부 블록 (59×42×10mm, 어댑터 플레이트 호환) ──
    color([0.2, 0.2, 0.2]) difference() {
        translate([-X_BLOCK_L/2, -X_BLOCK_W/2, 0])
            cube([X_BLOCK_L, X_BLOCK_W, 10]);
        // M4 관통 볼트홀 (20×32mm 피치, 도면 매칭)
        for(x = [-X_PITCH_X/2, X_PITCH_X/2])
            for(y = [-X_PITCH_Y/2, X_PITCH_Y/2])
                translate([x, y, -1]) cylinder(d=4.5, h=12);
    }
    // ── ② 리드넛 하우징 (하방 돌출, 스크류 라인 도달) ──
    color([0.18, 0.18, 0.18])
        translate([-12, -10, -15]) cube([24, 20, 15]);
    // ── ③ 레일 가이드 슈 (하부 양측, 레일 상면 양 가장자리 주행) ──
    color([0.15, 0.15, 0.15])
        for(sy = [-1, 1])
            translate([-X_BLOCK_L/2, sy * 15 - 5, -5])
                cube([X_BLOCK_L, 10, 5]);
}
module water_reservoir_tank() { TANK_X = 180; TANK_Y = 330; TANK_H = 80; color([0.1, 0.5, 0.8, 0.4]) { difference() { cube([TANK_X, TANK_Y, TANK_H]); translate([4, 4, 4]) cube([TANK_X - 8, TANK_Y - 8, TANK_H]); } } color([0.2, 0.6, 1.0, 0.3]) translate([4, 4, 4]) cube([TANK_X - 8, TANK_Y - 8, 55]); }
module teflon_washer_dummy() { color([0.9, 0.9, 0.9]) cylinder(d=BOSS_OD, h=WASHER_T); }  // ø35 × 1T 테프론 원판 (기성품, 홀 없음)
// =========================================================================
// GT2 타이밍 벨트 시각화 (모터 풀리 ↔ 중단 허브 벨트 림)
// =========================================================================
module gt2_belt_visual() {
    // 풀리 중심 좌표 (절대)
    BX = REVOLVER_CX;  BY = 0;                  // 큰 풀리 (중단 허브 벨트 림, 리볼버 축)
    SX = BELT_MOTOR_X;     SY = BELT_MOTOR_Y;   // 작은 풀리 (모터)
    FLOAT_H = BOSS_H + WASHER_T - 10;   // 리볼버 Z 오프셋
    BZ = MID_HUB_Z + FLOAT_H + (HUB_H - GT2_BELT_W) / 2;  // 벨트 Z 높이 (허브 중심 정렬)
    R1 = BIG_PULLEY_OD/2;
    R2 = SMALL_PULLEY_OD/2;
    BT = 1.5;  // 벨트 두께

    // 두 중심 간 거리 및 각도
    D = sqrt(pow(SX-BX,2) + pow(SY-BY,2));
    PHI = atan2(SY - BY, SX - BX);
    // 외접선 접점각: theta = PHI ± acos((R1-R2)/D)
    BETA = acos((R1 - R2) / D);
    T_UP = PHI + BETA;     // 상부 접선 접점각
    T_DN = PHI - BETA;     // 하부 접선 접점각

    color([0.12, 0.12, 0.12, 0.7]) {
        // ── 큰 풀리 감김 (벨트 링) ──
        translate([BX, BY, BZ]) difference() {
            cylinder(d=BIG_PULLEY_OD + BT*2, h=GT2_BELT_W);
            translate([0, 0, -1]) cylinder(d=BIG_PULLEY_OD, h=GT2_BELT_W + 2);
            // 접선 사이 구간 제거 (모터 쪽 열림)
            hull() {
                translate([R1*cos(T_UP), R1*sin(T_UP), -1]) cylinder(d=BT*3, h=GT2_BELT_W+2);
                translate([R1*cos((T_UP+T_DN)/2)*1.5, R1*sin((T_UP+T_DN)/2)*1.5, -1]) cylinder(d=BT*3, h=GT2_BELT_W+2);
                translate([R1*cos(T_DN), R1*sin(T_DN), -1]) cylinder(d=BT*3, h=GT2_BELT_W+2);
            }
        }
        // ── 작은 풀리 감김 (벨트 링) ──
        translate([SX, SY, BZ]) difference() {
            cylinder(d=SMALL_PULLEY_OD + BT*2, h=GT2_BELT_W);
            translate([0, 0, -1]) cylinder(d=SMALL_PULLEY_OD, h=GT2_BELT_W + 2);
        }
        // ── 상부 접선 직선 ──
        hull() {
            translate([BX + R1*cos(T_UP), BY + R1*sin(T_UP), BZ])
                cylinder(d=BT, h=GT2_BELT_W);
            translate([SX + R2*cos(T_UP), SY + R2*sin(T_UP), BZ])
                cylinder(d=BT, h=GT2_BELT_W);
        }
        // ── 하부 접선 직선 ──
        hull() {
            translate([BX + R1*cos(T_DN), BY + R1*sin(T_DN), BZ])
                cylinder(d=BT, h=GT2_BELT_W);
            translate([SX + R2*cos(T_DN), SY + R2*sin(T_DN), BZ])
                cylinder(d=BT, h=GT2_BELT_W);
        }
    }
}