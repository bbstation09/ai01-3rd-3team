# AutoHotkey 사용 가이드

## 1. 실행 준비 사항 (필수)
이 매크로(`time_click.ahk`)는 **AutoHotkey v2.0 이상**의 최신 버전에서 작동하도록 제작되었습니다.

### 설치 방법
1. **공식 사이트 접속**: [AutoHotkey.com](https://www.autohotkey.com/)
2. **Download** 버튼 클릭 -> **Download v2.0** 선택하여 설치 파일 다운로드
3. 설치 파일 실행 후 **Install** 클릭
4. 설치 완료 후 별도의 설정 없이 바로 `.ahk` 파일을 더블 클릭하여 실행 가능합니다.

> ⚠️ **주의**: v1.1 버전(구 버전)이 이미 설치되어 있다면 v2.0과 문법이 달라 실행되지 않을 수 있습니다. 반드시 v2.0 이상을 설치해주세요.

---

## 2. 캡차 자동 입력 기능 준비 사항 (선택)
캡차(Captcha) 자동 입력 기능을 사용하려면 **Python**과 **OCR(광학 문자 인식) 프로그램** 설정이 필요합니다.

### 2.1 Python 설치 및 라이브러리 설정
1. **Python 설치**: [Python 공식 홈페이지](https://www.python.org/)에서 Python을 설치합니다. (설치 시 "Add Python to PATH" 체크 필수)
2. **필수 라이브러리 설치**: 터미널(CMD)에서 아래 명령어를 실행하여 필요한 패키지를 설치합니다.
   ```bash
   pip install Pillow pytesseract
   ```

### 2.2 Tesseract-OCR 설치 (필수)
이미지 내 글자를 인식하기 위해 Tesseract 엔진이 필요합니다.
1. **다운로드**: [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) (Windows용 설치 파일)
2. **설치**: 다운로드한 exe 파일을 실행하여 설치합니다.
   - 기본 설치 경로: `C:\Program Files\Tesseract-OCR`
   - 만약 다른 경로에 설치했다면 `captcha_solver.py` 파일 내의 경로 설정을, 설치한 경로로 수정해야 합니다.

### 2.3 필수 이미지 파일 준비
캡차 인식 영역을 찾기 위해 기준이 되는 이미지("앵커")가 필요합니다.
- 파일명: `refresh_icon.png` (캡차 옆의 새로고침 아이콘 등을 캡처)
- 위치: `swords/images/refresh_icon.png` 에 저장

---

## 3. AutoHotkey란?
**AutoHotkey(오토핫키)**는 윈도우 환경에서 키보드와 마우스 동작을 자동화해주는 강력한 오픈 소스 스크립트 언어입니다.

### 주요 특징
- **강력한 자동화**: 단순한 키 매핑부터 복잡한 GUI 매크로까지 구현 가능
- **가벼운 리소스**: 매우 적은 메모리 점유율
- **자유로운 제어**: 윈도우 창 제어, 이미지 검색, 파일 관리 등 다양한 시스템 기능 제어 가능
- **무료**: 누구나 무료로 사용할 수 있는 오픈 소스 소프트웨어

이 프로젝트의 `time_click.ahk`는 AutoHotkey의 GUI 기능과 이미지 서치 기능을 활용하여 제작된 티켓팅 자동화 스크립트입니다.
