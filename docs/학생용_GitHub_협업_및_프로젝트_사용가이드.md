# 📘 음향 형상 역추적 프로젝트 학생용 GitHub 협업 가이드

본 가이드는 학생 연구진이 **공유 깃허브 계정(`junramhoei-spec`)**을 활용하여 연구 프로젝트(`acoustic_simulation`)를 본인 컴퓨터에 다운로드하고 실행하며, 최신 코드를 주고받는 방법(**GitHub Desktop 프로그램**, **웹사이트**, **터미널**)을 상세히 설명합니다.

---

## 📌 1. 저장소 기본 정보

- **깃허브 원격 저장소 URL**: `https://github.com/junramhoei-spec/acoustic_simulation`
- **공유 깃허브 계정 아이디**: `junramhoei-spec`
- **연동 이메일**: `junramhoei@gmail.com`
- **주요 실행 파일**: `V2/app.py` (Streamlit 웹 대시보드)

---

## 🖥️ 방법 1: GitHub Desktop 앱 사용 (초보자 강력 추천 ⭐)

터미널 명령어가 익숙하지 않은 학생들은 버튼 클릭만으로 작업할 수 있는 **GitHub Desktop 프로그램** 사용을 권장합니다.

### 1-1. 프로그램 설치 및 로그인
1. [desktop.github.com](https://desktop.github.com) 에 접속하여 **GitHub Desktop**을 다운로드 및 설치합니다.
2. 실행 후 `Sign in to GitHub.com` 클릭 ➜ 공유 계정(`junramhoei-spec` / `junramhoei@gmail.com`)으로 로그인합니다.

### 1-2. 처음 프로젝트 내 컴퓨터로 가져오기 (Clone)
1. 상단 메뉴 `File` ➜ `Clone repository...` 클릭
2. `URL` 탭 선택 ➜ Repository URL에 `https://github.com/junramhoei-spec/acoustic_simulation` 입력
3. `Local path`에 내 컴퓨터에서 저장할 폴더 경로 선택 후 **[Clone]** 클릭

### 1-3. 매일 작업 시작 전 최신 코드 받기 (Pull)
- 상단 메뉴의 **[Fetch origin]** 또는 **[Pull origin]** 버튼을 클릭하면 다른 학생이 올린 최신 코드가 내 컴퓨터로 자동 반영됩니다.

### 1-4. 작업 완료 후 올리기 (Commit & Push)
1. 코드나 3D CAD 파일(`*.scad`)을 수정/추가하면 GitHub Desktop 화면 좌측에 변경된 파일 목록이 자동으로 나타납니다.
2. 좌측 하단 **Summary** 칸에 작업 내용(예: "2번 컵 수위 보정 및 3D CAD 추가")을 간단히 적습니다.
3. **[Commit to master]** 버튼 클릭 ➜ 상단 **[Push origin]** 버튼 클릭하면 깃허브로 업로드 완료!

---

## 🌐 방법 2: GitHub 웹사이트(Web UI) 사용 (웹에서 직접 업로드/수정)

프로그램 설치 없이 웹 브라우저에서 바로 파일이나 3D CAD 모델을 업로드하거나 수정할 수 있습니다.

### 2-1. 새 파일/CAD 모델 올리기
1. [https://github.com/junramhoei-spec/acoustic_simulation](https://github.com/junramhoei-spec/acoustic_simulation) 접속
2. 파일을 올릴 대상 폴더(예: `v2/parts/`)로 이동
3. 우측 상단 **[Add file]** ➜ **[Upload files]** 클릭
4. 올릴 파일들을 드래그 앤 드롭한 후, 아래 **[Commit changes]** 버튼 클릭!

### 2-2. 웹에서 직접 코드/문서 수정하기
1. 수정할 파일(예: `README.md` 또는 `*.py`) 클릭
2. 우측 상단 **연필(Edit this file)** 아이콘 클릭하여 수정
3. 수정 완료 후 우측 상단 **[Commit changes...]** ➜ **[Commit changes]** 클릭!

---

## 💻 방법 3: 터미널 커맨드라인 사용 (CLI)

개발자용 명령어를 이용하는 방법입니다.

### 3-1. 처음 받아오기 (Clone)
```bash
git clone https://github.com/junramhoei-spec/acoustic_simulation.git
cd acoustic_simulation
pip install torch numpy matplotlib streamlit pandas
```

### 3-2. 매일 작업 전 최신 코드 받아오기 (Pull)
```bash
git pull
```

### 3-3. 내 작업 완료 후 올리기 (Push)
```bash
git status
git add .
git commit -m "작업내용: 2번 컵 역추적 파라미터 보정"
git push origin master
```

---

## ▶️ 프로젝트 대시보드 실행 방법 (공통)

어떤 방법으로 코드를 받았든, 터미널이나 VS Code 터미널에서 아래 명령어를 실행하면 웹 대시보드가 열립니다:

```bash
streamlit run V2/app.py
```

---

## 🚨 자주 묻는 질문 및 주의사항 (FAQ)

1. **Q. 대용량 데이터 파일(`*.npz`)이나 실행 파일(`*.exe`)도 올라가나요?**
   - **아닙니다.** 대용량 데이터나 실행 파일은 `.gitignore`에 의해 자동으로 제외되므로, 소스 코드와 3D CAD 모델만 안심하고 올리시면 됩니다.
2. **Q. 코드를 올릴 때 충돌(Conflict) 경고가 떠요!**
   - 내가 올리기 전에 다른 학생이 먼저 코드를 올린 경우입니다. **[Pull origin]** (또는 `git pull`)을 먼저 눌러 최신 코드를 받아온 후 다시 Push 하시면 됩니다.
