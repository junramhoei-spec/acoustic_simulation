# 🔊 Acoustic Shape Reconstruction V2 (음향 기반 컵 형상 역추적 프로젝트)

이 프로젝트는 **물 채움 시 수위 변화에 따른 음향 공명 주파수(Dip Spectrum / Ratio Transfer Function)** 데이터를 기반으로 컵의 **높이($H$) 및 3D 반지름 프로파일($r(z)$)**을 역추적하는 딥러닝 프레임워크입니다.

---

## 🌟 주요 기능 (Key Features)

1. **순방향 음향 공명 탐색기 (Forward Explorer)**
   - Transfer Matrix Method (TMM) 음향 관 모델링 기반 딥 스펙트럼 합성
   - 물 주입 시퀀스에 따른 음향 워터폴 스펙트로그램 시각화
2. **전문가 결합 모델 (Ensemble Prediction)**
   - 높이 전문가 ($H$ Expert: `rnn_sline_nodetach_bestH.pt`)
   - 반지름 전문가 ($r$ Expert: `rnn_sline_uni.pt`)
   - 25개 10mm 슬롯 피치 등가반지름 계단 프로파일 복원
3. **20종 실측 세션 자동 일괄 평가**
   - 실측 데이터셋 자동 로드 및 실시간 역추정
   - 음향 공명 스펙트로그램 + 참값(True GT) vs 예측(Pred) 1:1 시각화 비교

---

## 🚀 빠른 시작 (Quick Start)

### 1. 필수 패키지 설치
```bash
pip install torch numpy matplotlib streamlit pandas
```

### 2. Web GUI 대시보드 실행
```bash
streamlit run V2/app.py
```

---

## 📁 디렉토리 구조 (Repository Layout)

```
acoustic_simulation_repo/
├── V2/                         # Streamlit 앱 및 핵심 역추적 파이프라인
│   ├── app.py                  # Streamlit 통합 웹 앱 실행 파일
│   ├── real_measured_json_all/ # 20종 실측 JSON 데이터셋
│   └── create_report_docx_v4.py# 보고서 생성 스크립트
├── v2/                         # 알고리즘 핵심 패키지
│   ├── config.py               # 음향 물리 상수 및 모델 설정
│   ├── combine.py              # 앙상블 조합 추론기 (CombinedPredictor)
│   ├── forward/                # TMM 순방향 시뮬레이터 (tmm.py)
│   └── data/                   # 데이터 로더 및 전처리 모듈 (loader.py, shapes.py)
├── dataset/
│   └── models_v2/              # 사전 학습된 PyTorch 체크포인트 (.pt)
├── README.md
└── .gitignore
```

---

## 📧 문의 및 정보
- Contact: `junramhoei@gmail.com`
