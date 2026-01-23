# 🚀 빠른 시작 가이드

## ⚡ 3분 안에 테스트하기

### 1️⃣ Extension 로드 (30초)

1. Chrome 열기
2. 주소창에 입력: `chrome://extensions/`
3. 우측 상단 **"개발자 모드"** ON
4. **"압축해제된 확장 프로그램을 로드합니다"** 클릭
5. 폴더 선택: `c:\HDCLab\ai01-3rd-3team\swords\chrome-extension`

**⚠️ 아이콘 오류 발생 시:**
- 일단 무시하고 진행 (나중에 추가 가능)
- 또는 아무 PNG 파일을 `icons/icon16.png`, `icons/icon48.png`, `icons/icon128.png` 이름으로 복사

---

### 2️⃣ 테스트 페이지 열기 (10초)

server.bat 실행 후 localhost:5000에서 테스트
페이지 올리기.
---

### 3️⃣ Extension 시작 (20초)

1. **F12** (개발자 도구 열기) → **Console** 탭
2. Extension 아이콘 클릭 (또는 없으면 Extensions 메뉴)
3. Popup에서:
   - Target Time: **현재 시간** (즉시 실행)
   - Seat Count: `1`
   - **Start** 버튼 클릭

---

### 4️⃣ 자동화 관찰 (1분)

Console에서 로그 확인:
```
[INFO] SWORD_AUTOMATION_INIT
[INFO] STATE_TRANSITION {from: "IDLE", to: "CLICK_START"}
[INFO] RESERVE_BUTTON_CLICKED
[INFO] POPUP_DETECTED
[INFO] POPUP_CLOSED_VIA_BUTTON
[INFO] STATE_TRANSITION {to: "SELECT_SEAT"}
...
```

**페이지에서 자동으로:**
1. ✅ "예매하기" 버튼 클릭
2. ✅ 팝업 닫기
3. ✅ 구역 선택 (VIP)
4. ✅ 좌석 클릭
5. ✅ 확인 버튼 클릭
6. ✅ 결제 페이지 도달 → **SUCCESS!**

---

## 🔍 Debug 모드 활성화

Popup에서 **"Debug overlay"** 체크하면 페이지 좌하단에 실시간 상태 표시:
```
🗡️ SWORD Debug
State: SELECT_SEAT
Retries: 0
Time: 0:15
```

---

## ❌ 문제 발생 시

### "Content script not loaded"
→ **페이지 새로고침** (F5)

### Console에 로그 없음
→ `chrome://extensions/` → Extension 카드 → **Details** → **"파일 URL에 대한 액세스 허용"** ON

### Extension 로드 오류
→ Errors 클릭 → manifest.json 오류 확인

---

## ✅ 성공 확인

Console에 이 메시지가 나오면 성공:
```
[INFO] PAYMENT_SUCCESS
```

페이지가 자동으로 "결제 화면"까지 도달하면 테스트 완료! 🎉

---

## 📚 다음 단계

- [TESTING.md](TESTING.md) - 상세한 테스트 시나리오
- [ARCHITECTURE.md](ARCHITECTURE.md) - 아키텍처 이해
- [README.md](README.md) - 전체 문서

**실제 사이트 적용은 TESTING.md Step 5 참고!**
