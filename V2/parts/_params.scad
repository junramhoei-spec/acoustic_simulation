// =========================================================================
// 공유 파라미터 (모든 개별 부품 파일에서 include)
// 메인 어셈블리: cup_z_x_catrage_frame_water_mic_anti_3030.scad 에서 추출
// 프레임: 600 × 420 × 700mm (3030 프로파일, Y=0 대칭)
// =========================================================================

$fn = 60;  // 부품 출력용 고해상도
GLOBAL_TOLERANCE = 0.2;

// --- [1] 하부 기성품 및 원통 파라미터 ---
X_RAIL_LEN = 290.0;
X_BLOCK_W = 30.0; X_BLOCK_L = 32.0;   // 신규 X슬라이더 블록 (폭 30mm × 길이 32mm)
X_PITCH_X = 20.0; X_PITCH_Y = 20.0;   // 체결 홀 피치 (20 × 20mm, M3 나사탭 4개)
X_RAIL_W = 30.0;  X_RAIL_H = 20.0;   // 레일 폭 30mm (레일 바닥~블록 윗면 높이 29mm 반영)
X_TOTAL_H = 29.0;                    // 레일 바닥에서 슬라이더 블록 윗면까지의 높이

MOTOR_W = 42.0;      MOTOR_PITCH = 31.0; MOTOR_HOLE_D = 3.5;    
MOTOR_BOSS_D = 22.0; MOTOR_BOSS_H = 2.0; SCREW_D = 8.0;         
MOT_BODY_L = 41.0;   SHAFT_L = 24.0;     // 실측 NEMA17 몸통 41mm / 축 돌출 24mm

CUP_ID = 99.5;  CUP_WALL = 5.0; CUP_OD = 110.0;     // 아크릴 원통 OD110/ID100
CUP_H = 180.0;   CAGE_H = 60.0;  FLOOR_H = 10.0; PISTON_H = 20.0;     

LIP_D = 30.0;    LIP_H = 5.0;    LEAK_DRAIN_D = 4.0;    
GUIDE_PIPE_D = 8.0; BUSHING_OD = 12.0; BUSHING_H = 8.0;       
DRAIN_RADIUS = 35.0; DRAIN_D = 8.0;        

Y_OFFSET = 85.0; BRKT_H = 12.0; BRKT_D = 122.0; BRKT_ID = 62.0; Z_MOUNT_PCD = 86.0;   

// --- [2] 아크릴 파이프 및 상부 카트리지 ---
ACRYL_ID = 100.0; ACRYL_T = 5.0; ACRYL_OD = ACRYL_ID + (ACRYL_T * 2);  // OD110 (아크릴집 106 재고없음 → 컵과 동일 규격)

REVOLVER_PCD = 240.0;     // 인접 카트리지 웹 9.8mm 확보 (OD110 대응, 230→240)
CARTRIDGE_OD = REVOLVER_PCD + ACRYL_OD + 8; 
TOP_PLATE_H = 15.0;       // 아크릴 15T 통판 (보스홀 단 깊이 10mm)

HUB_D = 60.0;            
SHAFT_D = 12.0;          
HUB_WALL = 4.0;          
HUB_H = 15.0;             // 아크릴 5T × 3장 적층 — 파이프 130mm 대응
POCKET_DEPTH = 5.0;
MID_HUB_Z = 63.5;          // 중단 허브 하면 Z (벨트 중심 Z=71.0mm 정렬, 풀리 상단 Z=75.0mm = 축상단-1mm)
UPPER_HUB_Z = 135.0;       // 상단 허브 하면 Z (전체 135+15=150 유지)
BOSS_OD = 35.0;
BOSS_H = 11.0;             // 보스11 + 와셔1 = 12, 리세스10 → 허브 2mm 공중

// --- [3] GT2 벨트 구동 시스템 ---
GT2_PITCH     = 2.0;
GT2_BELT_W    = 6.0;
BIG_PULLEY_TEETH = 566;
BIG_PULLEY_PD = BIG_PULLEY_TEETH * GT2_PITCH / PI;
BIG_PULLEY_OD = BIG_PULLEY_PD + 1.0;
SMALL_PULLEY_TEETH = 20;
SMALL_PULLEY_PD = SMALL_PULLEY_TEETH * GT2_PITCH / PI;
SMALL_PULLEY_OD = SMALL_PULLEY_PD + 1.0;

BELT_MOTOR_X = -300;
BELT_MOTOR_Y = -155.5;
BRKT_MOTOR_H = 25.0;
BRKT_MOTOR_W = 45.0;        // 브래킷 폭 45mm (프로파일 간섭 회피 복원)
SLOT_LEN = 10.0;
FLAG_W = 15.0;  FLAG_H = 8.0;  FLAG_T = 1.5;

X_POS_MEASURE = 170.0;   // 측정 브래킷 X좌표 (X_M~X_R 정중앙, X대칭)

// --- [4] 3030 프레임 경계 (600×430×700mm) ---
PF = 30;             // 3030 알루미늄 프로파일
WASHER_T = 1.0;     

X_L = -320;
X_M = 60;
X_R = 250;
Y_F = -210;          // 전방 (대칭: -210+30=-180, Y=0 중심)
Y_B = 180;           // 후방 (대칭: 180+30=210, Y=0 중심) — 메인파일과 동기화

Z_BOT = -480;
Z_RAIL = -322;
Z_MID = -TOP_PLATE_H - PF;
Z_TOP = 220;

SUPPORT_PILLAR_H = Z_TOP - PF;

SHAFT_SQ = 20;       // 2020 사각 회전축

// 사각 축 홀 크기
SQ = SHAFT_SQ + GLOBAL_TOLERANCE;  // 20.2mm

// --- 리볼버/컵 축 정렬 (보스홀=판 중심에 리볼버 정렬) ---
REVOLVER_CX = (X_L + X_M + PF)/2;        // 판 중심 = 보스홀 = 리볼버 회전축 (-115)
DROP_X      = REVOLVER_CX + REVOLVER_PCD/2;  // 링 드롭 / 컵 적재 축 (+5)

FLANGE_Z = 52.0;       // 모터 전면 안착 높이 (Z=52mm -> 축 상단 Z=76mm, 풀리 결합)

// --- [5] 모터 체결홀 (이미 제작 완료된 15T 상판 원본 도면 수치 100% 유지) ---
MOTOR_BOLT_PITCH     = 25.0;      // Y피치 (Y = ±12.5mm)
MOTOR_BOLT_X_NOMINAL = X_L + 55;  // 1열: 상판 좌단 55 (모터축 기준 +35mm = X=-265mm)
MOTOR_BOLT_X_SHIFT   = X_L + 40;  // 2열: 상판 좌단 40 (모터축 기준 +20mm = X=-280mm)

// 모터 마운트 볼트 카운터보어 (단볼트용 — 브래킷 두께 25 중 깊게 파냄)
MOTOR_CB_D     = 6.5;            // M3 캡볼트 머리 클리어런스
MOTOR_CB_DEPTH = 19;             // 카운터보어 깊이 (잔여 통과 6mm → M3×10 단볼트)
