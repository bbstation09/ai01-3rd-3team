# 🧪 Chrome Extension 테스트 가이드

## 1단계: 아이콘 준비 (임시)

가장 빠른 방법은 텍스트 아이콘 생성:

```bash
cd c:\HDCLab\ai01-3rd-3team\swords\chrome-extension\icons
```

**또는** 온라인 생성기 사용:
- https://favicon.io/ → "🗡️" 이모지 → Download → 압축 풀어서 icons/ 에 복사

**임시 방법**: 아무 PNG 파일을 복사해서 `icon16.png`, `icon48.png`, `icon128.png` 이름으로 저장

---

## 2단계: Extension 로드

1. **Chrome 열기**
2. 주소창에 입력: `chrome://extensions/`
3. 우측 상단 **"개발자 모드"** 활성화
4. **"압축해제된 확장 프로그램을 로드합니다"** 클릭
5. `c:\HDCLab\ai01-3rd-3team\swords\chrome-extension` 폴더 선택
6. ✅ Extension이 목록에 나타나면 성공!

**오류 발생 시**:
- Manifest 오류 → 콘솔에서 상세 확인
- 아이콘 없음 오류 → 아이콘 파일 추가
- `Errors` 클릭해서 상세 로그 확인

---

## 3단계: 테스트 페이지 준비

### 옵션 A: Mock 테스트 페이지 (추천)

`chrome-extension/test/mock-ticket-page.html` 생성:

```html
<!DOCTYPE html>
<html>
<head>
  <title>Mock Ticket Page</title>
  <style>
    body { font-family: Arial; padding: 20px; }
    .btn { padding: 10px 20px; margin: 10px; cursor: pointer; }
    .seat { width: 40px; height: 40px; margin: 5px; display: inline-block;
            background: #4CAF50; cursor: pointer; border: 1px solid #333; }
    .seat.sold { background: #999; cursor: not-allowed; }
    .seat.selected { background: #ff9800; }
    .popup { display: none; position: fixed; top: 50%; left: 50%;
             transform: translate(-50%, -50%); background: white;
             padding: 30px; border: 2px solid #333; z-index: 999; }
    .overlay { display: none; position: fixed; top: 0; left: 0;
               width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 998; }
  </style>
</head>
<body>
  <h1>Mock Ticketing Site</h1>
  
  <!-- Stage 1: Reserve Button -->
  <div id="stage1">
    <h2>Stage 1: 예매하기</h2>
    <button id="btnReserve" class="btn">예매하기</button>
  </div>

  <!-- Popup (appears after clicking reserve) -->
  <div class="overlay" id="overlay"></div>
  <div class="popup" id="popup">
    <h3>안내</h3>
    <p>좌석을 선택하세요</p>
    <button class="btn" onclick="closePopup()">확인</button>
  </div>

  <!-- Stage 2: Seat Selection (hidden initially) -->
  <div id="stage2" style="display:none;">
    <h2>Stage 2: 좌석 선택</h2>
    <div id="seats"></div>
    <button id="btnConfirm" class="btn" style="display:none;">좌석선택완료</button>
  </div>

  <!-- Stage 3: Payment (hidden initially) -->
  <div id="stage3" style="display:none;">
    <h2>Stage 3: 결제</h2>
    <p>✅ 좌석 선택이 완료되었습니다!</p>
    <div id="payment-form">Payment Page Mock</div>
  </div>

  <script>
    // Reserve button click
    document.getElementById('btnReserve').addEventListener('click', () => {
      // Show popup
      document.getElementById('overlay').style.display = 'block';
      document.getElementById('popup').style.display = 'block';
    });

    function closePopup() {
      document.getElementById('overlay').style.display = 'none';
      document.getElementById('popup').style.display = 'none';
      
      // Show stage 2
      document.getElementById('stage1').style.display = 'none';
      document.getElementById('stage2').style.display = 'block';
      
      // Generate seats
      generateSeats();
    }

    function generateSeats() {
      const container = document.getElementById('seats');
      for (let i = 0; i < 50; i++) {
        const seat = document.createElement('div');
        seat.className = i % 7 === 0 ? 'seat sold' : 'seat';
        seat.dataset.seatId = 'seat-' + i;
        seat.dataset.row = Math.floor(i / 10);
        seat.dataset.col = i % 10;
        
        seat.addEventListener('click', function() {
          if (!this.classList.contains('sold')) {
            this.classList.toggle('selected');
            checkSelection();
          }
        });
        
        container.appendChild(seat);
      }
    }

    function checkSelection() {
      const selected = document.querySelectorAll('.seat.selected');
      const btn = document.getElementById('btnConfirm');
      btn.style.display = selected.length > 0 ? 'block' : 'none';
    }

    document.getElementById('btnConfirm').addEventListener('click', () => {
      const selected = document.querySelectorAll('.seat.selected');
      if (selected.length > 0) {
        // Go to payment
        document.getElementById('stage2').style.display = 'none';
        document.getElementById('stage3').style.display = 'block';
        
        // Change URL to simulate navigation
        history.pushState({}, '', '/payment');
      }
    });
  </script>
</body>
</html>
```

### 옵션 B: 실제 사이트 테스트

**주의**: 실제 티켓팅 사이트에서 테스트 시 주의사항
- 테스트 전용 계정 사용
- 실제 결제 진행 금지
- 서버에 부담 주지 않도록 주의

---

## 4단계: 단계별 테스트

### Test 1: Extension 로드 확인

1. Mock 페이지 열기: `file:///c:/HDCLab/ai01-3rd-3team/swords/chrome-extension/test/mock-ticket-page.html`
2. **F12** → Console 탭
3. 확인해야 할 로그:
   ```
   [INFO] SWORD_AUTOMATION_INIT
   [INFO] STATES_REGISTERED {count: 10}
   [INFO] INITIALIZATION_COMPLETE
   ```

**오류 발생 시**:
- `Uncaught ReferenceError` → 스크립트 로드 순서 문제, manifest.json 확인
- `Content script not loaded` → 페이지 새로고침

### Test 2: 수동 상태 전환 테스트 (Console)

```javascript
// FSM 접근 확인
window.SwordAutomation

// 현재 상태 확인
window.SwordAutomation.fsm.getState()

// 수동 전환 테스트
window.SwordAutomation.fsm.transition('CLICK_START')

// 로그 확인
logger.getLogs()
```

### Test 3: Popup UI 테스트

1. Extension 아이콘 클릭
2. Popup이 열리는지 확인
3. 각 필드 입력:
   - Target Time: `10:30:00`
   - Seat Count: `1`
4. **Start** 버튼 클릭
5. Console에서 로그 확인:
   ```
   [INFO] START_REQUESTED
   [INFO] STATE_TRANSITION {from: "IDLE", to: "WAIT_OPEN"}
   ```

### Test 4: 자동화 플로우 테스트

**시나리오**: 즉시 실행 (Target Time = 현재 시간)

1. Popup에서 현재 시간 입력
2. **Start** 클릭
3. 예상 흐름:
   ```
   IDLE → CLICK_START → (버튼 클릭) → HANDLE_POPUP → 
   (팝업 닫기) → SELECT_SEAT → (좌석 클릭) → CONFIRM → PAYMENT
   ```

4. **Debug 모드 활성화**:
   - Popup에서 "Debug overlay" 체크
   - 페이지 좌하단에 상태 표시 확인

5. **로그 확인**:
   - Popup → "View Logs" 클릭
   - 각 상태 전환이 기록되는지 확인

### Test 5: 에러 복구 테스트

**시나리오**: 버튼이 없는 페이지

1. 빈 페이지 열기 (`about:blank`)
2. Extension 시작
3. 예상 동작:
   - `CLICK_START` → Element not found
   - Recovery Manager 동작
   - 최대 5번 재시도
   - `ERROR` → `FAILED` 전환

4. 콘솔에서 확인:
   ```javascript
   logger.getLogs({level: 'ERROR'})
   ```

---

## 5단계: 실제 사이트 적용

### Interpark 테스트 (예시)

1. **Selector 확인 먼저**:
   ```javascript
   // Interpark 페이지에서 F12 → Console
   document.querySelector('#ProductForm .btn_Booking') // 예매 버튼
   document.querySelectorAll('.seat:not(.sold)') // 좌석들
   ```

2. **Config 업데이트** (`config/sites.js`):
   ```javascript
   selectors: {
     reserveButton: ['실제_셀렉터'],
     seats: ['실제_좌석_셀렉터'],
   }
   ```

3. **Extension 리로드**:
   - chrome://extensions/ → Reload 버튼 클릭

4. **테스트 실행**:
   - Interpark 페이지 열기
   - Extension 시작
   - Debug 모드로 상태 모니터링

---

## 디버깅 팁

### 1. 상태가 진행되지 않을 때

```javascript
// 현재 상태 확인
window.SwordAutomation.fsm.currentState

// 마지막 에러 확인
window.SwordAutomation.fsm.context.errors

// 수동으로 다음 상태로 이동
window.SwordAutomation.fsm.transition('다음_상태_이름')
```

### 2. Element를 못 찾을 때

```javascript
// Selector 테스트
smartSelect(getSiteConfig().selectors.reserveButton)

// 모든 매칭 시도
getSiteConfig().selectors.reserveButton.forEach(sel => {
  console.log(sel, document.querySelector(sel))
})
```

### 3. 로그 내보내기

```javascript
// 로그를 파일로 저장
const logs = logger.exportLogs();
const blob = new Blob([logs], {type: 'application/json'});
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'sword-logs.json';
a.click();
```

---

## 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| Extension이 안 보임 | Manifest 오류 | chrome://extensions에서 Errors 확인 |
| Console에 로그 없음 | Content script 미주입 | 페이지 새로고침, manifest matches 확인 |
| 상태 전환 안됨 | Selector 오류 | F12에서 selector 직접 테스트 |
| Popup 안 열림 | popup.html 경로 오류 | manifest.json 경로 확인 |

---

## 다음 단계

테스트 성공 후:
1. ✅ Selector 정확도 높이기 (실제 사이트에 맞춰)
2. ✅ Error recovery 전략 튜닝
3. ✅ VLM 통합 (CAPTCHA, 팝업 처리)
4. ✅ 성능 최적화 (타이밍, 재시도 간격)

---

**이제 시작해보세요!** 🚀
