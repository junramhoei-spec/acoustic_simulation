# 📘 음향 형상 역추적 프로젝트 학생용 GitHub 협업 가이드

본 가이드는 학생 연구진이 **공유 깃허브 계정(`junramhoei-spec`)**을 활용하여 본 연구 프로젝트(`acoustic_simulation`)를 본인 컴퓨터에 다운로드하고, 실행하며, 최신 코드를 주고받는(Pull / Push) 방법을 상세히 설명합니다.

---

## 📌 1. 저장소 기본 정보

- **깃허브 원격 저장소 URL**: `https://github.com/junramhoei-spec/acoustic_simulation`
- **공유 깃허브 계정 아이디**: `junramhoei-spec`
- **연동 이메일**: `junramhoei@gmail.com`
- **주요 실행 파일**: `V2/app.py` (Streamlit 웹 대시보드)

---

## 📥 2. 1단계: 내 컴퓨터로 프로젝트 처음 가져오기 (Clone)

터미널(PowerShell 또는 Command Prompt)을 열고 프로젝트를 다운로드할 폴더로 이동한 후 아래 명령어를 입력합니다.

```bash
# 1. 깃허브 저장소 복제 (Clone)
git clone https://github.com/junramhoei-spec/acoustic_simulation.git

# 2. 프로젝트 폴더로 이동
cd acoustic_simulation

# 3. 필수 라이브러리 설치
pip install torch numpy matplotlib streamlit pandas
```

---

## ▶️ 3. 2단계: 앱 대시보드 실행 (Run)

프로젝트 폴더(`acoustic_simulation`) 안에서 아래 명령어를 실행하면 웹 브라우저에서 분석 대시보드가 열립니다.

```bash
streamlit run V2/app.py
```

> **💡 앱 탭 구성**:
> - **1️⃣ 순방향 탐색기**: 컵 형상 변경에 따른 딥 스펙트럼 & 음향 워터폴 시각화
> - **4️⃣ 추론**: 20종 실측 데이터 세션 일괄 평가 및 스펙트로그램 / 3D 역추적 비교

---

## 🔄 4. 3단계: 작업 시작 전 필수! 최신 코드 받기 (Pull)

> **⚠️ 중요 (필독)**: 다른 학생이 코드를 올렸을 수 있으므로, **매일 작업 시작 전 항상 `git pull`을 먼저 실행**해야 충돌을 방지할 수 있습니다.

```bash
git pull
```

---

## 📤 5. 4단계: 내 작업 완료 후 깃허브에 올리기 (Commit & Push)

내가 코드를 수정하거나 3D CAD 모델(`*.scad`)을 추가한 후 깃허브로 올릴 때의 순서입니다.

```bash
# 1. 변경되거나 추가된 파일 상태 확인
git status

# 2. 변경 사항 스테이징
git add .

# 3. 작업 내용 기록 (커밋 메시지는 알아보기 쉽게 작성)
git commit -m "작업내용: 2번 컵 역추적 파라미터 보정"

# 4. 깃허브 원격 저장소로 업로드 (Push)
git push origin master
```

---

## 🔐 6. 5단계: 계정 로그인 인증 (새 컴퓨터에서 처음 Push 할 때)

새로운 컴퓨터에서 처음 `git push`를 실행할 때 계정 인증 창이 뜨면 다음 방법 중 하나로 처리합니다.

### 추천 방법: GitHub CLI (`gh`) 원클릭 브라우저 인증
```bash
# 1. GitHub CLI 설치 (Windows PowerShell 기준)
winget install --id GitHub.cli -e

# 2. 웹 브라우저 인증 실행
gh auth login
# ➜ GitHub.com 선택 ➜ HTTPS 선택 ➜ Y ➜ Login with a web browser 선택
# ➜ 표시되는 8자리 코드 복사 후 브라우저 창에서 입력 및 [Authorize] 버튼 클릭
```

---

## 🚨 7. 자주 묻는 질문 및 주의사항 (FAQ)

1. **Q. 대용량 데이터 파일(`*.npz`)이나 실행 파일(`*.exe`)도 올려야 하나요?**
   - **아닙니다.** 100MB가 넘는 대용량 데이터나 빌드 파일은 `.gitignore` 파일에 의해 자동으로 무시(제외)됩니다. 소스 코드(`*.py`, `*.json`, `*.scad`)와 학습된 체크포인트(`dataset/models_v2/*.pt`)만 올리시면 됩니다.
2. **Q. `git push` 시 충돌(Conflict) 오류가 나요!**
   - 내가 올리기 전에 다른 학생이 먼저 코드를 올린 경우입니다. `git pull`을 먼저 실행하여 최신 코드를 병합한 후 다시 `git push` 하세요.
