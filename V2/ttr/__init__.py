# -*- coding: utf-8 -*-
"""TTR(테스트타임 정제) 버전 레지스트리.

버전 규칙 (2026-08-04 확정):
  1. 손실 함수·매개변수화 등 '설계'가 바뀌면 버전을 올린다 (v0, v1, ...).
  2. iters, lr, λ 등 하이퍼파라미터는 버전 내부 '옵션'으로 둔다.
     → 버전 간 성능 비교표(ttr_rig10_results_{ver}.csv)가 설계 차이만 반영하도록.
  3. 보고서에 결과가 인용된 버전은 코드 동결(수정 금지). 개선은 다음 버전 파일로.

새 버전 추가 방법:
  v2/ttr/ttr_vN.py 에 동일 시그니처의 ttr_refine(spec_meas, v_cum, H0_mm, r0_mm,
  verbose=..., progress_cb=..., **opts) 를 구현하고 아래 VERSIONS에 한 줄 등록.
  → 앱 추론 탭의 'TTR 버전' 선택 상자에 자동으로 나타남.

공통 시그니처:
  입력  spec_meas: (S, 700) log10|H|, 생성 그리드(50~7000Hz 700bins)
        v_cum:     (S,) 누적 주입 부피 [m³]
        H0_mm, r0_mm: 초깃값 (NN 전문가 결합 예측, mm 단위)
  반환  (H_mm, r_mm(25,), delta_mm, loss_hist)
"""

VERSIONS = {
    "v0": {
        "module": "v2.ttr.ttr_v0",
        "desc": "잔차 MSE + 자유 δ(리그 유효길이) — 2026-08-04 동결",
        "opts": {
            "iters": 120,        # 최적화 반복 수
            "lr": 2e-3,          # Adam 학습률 (H 기준; r·δ는 2배)
            "lam_smooth": 3.0,   # 평활 정칙화 λ·Σ(Δr)²
            "delta0_mm": 10.0,   # δ 초깃값 (8월 리그 실증값)
            "w_step0": 1.0,      # 0스텝(빈 컵) 가중치
        },
    },
    "v1": {
        "module": "v2.ttr.ttr_v1",
        "desc": "다중 초깃값(NN/반전/원통, 잔차 MSE 선별) — 딥 앵커는 옵션(기본 OFF)",
        "opts": {
            "iters": 120,          # 본 최적화 반복 수
            "iters_screen": 40,    # 초깃값 선별용 짧은 최적화 반복 수 (×3 초깃값)
            "lr": 2e-3,            # Adam 학습률 (H 기준; r·δ는 2배)
            "lam_smooth": 3.0,     # 평활 정칙화
            "lam_res": 1.0,        # 잔차 MSE 가중 (v0 손실이 본체)
            "lam_dip": 0.0,        # 딥 위치 손실 가중 (0=비활성. 10mL 데이터에서 재평가)
            "beta": 30.0,          # soft-argmin 온도 (lam_dip>0일 때)
            "win_hz": 250.0,       # 딥 매칭 창 반폭 [Hz]
            "prom_th": 0.12,       # 실측 딥 검출 prominence 문턱 (log10 단위)
            "max_dips": 6,         # 스텝당 사용할 최대 딥 수
            "w_step0": 3.0,        # 0스텝(빈 컵) 딥 가중 — 바닥 앵커
            "delta0_mm": 10.0,     # δ 초깃값
        },
    },
}

DEFAULT_VERSION = "v0"


def get_refiner(version):
    """버전 문자열 → ttr_refine 함수 (지연 임포트: torch 로딩을 사용 시점까지 미룸)."""
    import importlib
    info = VERSIONS[version]
    mod = importlib.import_module(info["module"])
    return mod.ttr_refine


def default_opts(version):
    """해당 버전의 기본 옵션 사본."""
    return dict(VERSIONS[version]["opts"])
