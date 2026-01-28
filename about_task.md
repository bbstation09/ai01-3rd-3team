# Flow 기반 로그 시스템 전환 계획

## 📌 개요

### 현재 문제점
- **분산된 로그**: `perf`, `que`, `book` 세 가지 타입으로 분리
- **추적 어려움**: 한 사용자의 전체 예매 과정을 하나로 보기 힘듦
- **ML 학습 단위 불명확**: "이 예매 시도가 봇인가?"를 판단할 최소 단위가 애매함
- **이선좌 재시도**: 같은 session_id로 여러 번 시도하면 데이터가 비대해짐

### 해결책: Flow 기반 로그
- **하나의 예매 시도 = 하나의 flow_id = 하나의 JSON 파일**
- flow_id는 "공연 선택(예매하기 클릭)"에서 "결제 완료/이탈"까지
- 모든 단계의 데이터를 하나의 JSON에 통합

---

## 🎯 Flow의 생명주기

### Flow 시작
**시점**: 공연 목록 페이지(`/performances`)에서 **"예매하기" 버튼 클릭**  
**파일**: `perf_list.js`의 `goToQueue()` 함수

**이유**:
- ✅ 매크로의 진입 과정 포착 (어떻게 공연을 선택했는가)
- ✅ 대기열 진입 과정 포함
- ✅ 적절한 데이터 크기 (로그인부터는 너무 무거움)

### Flow 진행
```
[공연 목록: 예매하기 클릭] 
    ↓ flow_id 생성
[대기열] → [캡챠] → [구역 선택] → [좌석 선택] 
    → [할인 선택] → [예매자 정보] → [결제]
```

각 단계마다 `stages` 객체에 데이터를 누적

### Flow 종료
**시점**:
1. **성공**: 결제 완료 (`/step4/payment`의 완료 시)
2. **실패**: 
   - 중간 이탈 (`beforeunload` 이벤트)
   - 시간 초과
   - 이선좌로 포기

**최종 동작**: 서버로 전송 후 sessionStorage 삭제

---

## 📂 데이터 구조

### 전체 JSON 구조

```json
{
  "metadata": {
    // Flow 식별 정보
    "flow_id": "flow_20260128_abc123",
    "session_id": "sess_zxy987",
    "user_id": "user_id_001",
    "user_email": "test@example.com",
    "user_ip": "1.2.3.4",
    "created_at": "2026-01-28T12:00:00Z",
    
    // 공연 정보
    "performance_id": "perf001",
    "performance_title": "2026 아이유 콘서트",
    "selected_date": "2026-03-15",
    "selected_time": "18:00",
    
    // Flow 시간 정보
    "flow_start_time": "2026-01-28T12:00:00Z",
    "flow_end_time": "2026-01-28T12:05:30Z",
    "total_duration_ms": 330000,
    
    // 완료 상태
    "is_completed": true,
    "completion_status": "success",
    "final_seats": ["VIP-A25", "VIP-A26"],
    "booking_id": "BK20260128001",
    
    // 환경 정보 (한 번만 수집)
    "browser_info": {
      "userAgent": "Mozilla/5.0...",
      "webdriver": false,
      "platform": "Win32",
      "hardwareConcurrency": 8,
      "deviceMemory": 8,
      "screen": { "width": 1920, "height": 1080 },
      "viewport": { "w": 1920, "h": 1080 },
      "timezone": "Asia/Seoul"
    }
  },
  
  "stages": {
    "perf": { ... },
    "queue": { ... },
    "captcha": { ... },
    "section": { ... },
    "seat": { ... },
    "discount": { ... },
    "order_info": { ... },
    "payment": { ... }
  }
}
```

### Metadata 필드 설명

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `flow_id` | String | 이번 예매 시도 고유 ID | `"flow_20260128_abc123"` |
| `session_id` | String | 브라우저 세션 ID (여러 flow 공유 가능) | `"sess_zxy987"` |
| `user_id` | String | 사용자 고유 번호 | `"user_id_001"` |
| `user_email` | String | 사용자 이메일 | `"test@example.com"` |
| `user_ip` | String | 접속 IP (서버에서 설정) | `"1.2.3.4"` |
| `created_at` | ISO 8601 | Flow 생성 시각 | `"2026-01-28T12:00:00Z"` |
| `performance_id` | String | 공연 ID | `"perf001"` |
| `performance_title` | String | 공연 제목 | `"2026 아이유 콘서트"` |
| `selected_date` | String | 선택한 날짜 | `"2026-03-15"` |
| `selected_time` | String | 선택한 시간 | `"18:00"` |
| `flow_start_time` | ISO 8601 | Flow 시작 시각 | `"2026-01-28T12:00:00Z"` |
| `flow_end_time` | ISO 8601 | Flow 종료 시각 | `"2026-01-28T12:05:30Z"` |
| `total_duration_ms` | Number | 전체 소요 시간 (ms) | `330000` |
| `is_completed` | Boolean | 결제 완료 여부 | `true` |
| `completion_status` | String | 완료 상태 | `"success"` |
| `final_seats` | Array | 최종 선택 좌석 | `["VIP-A25"]` |
| `booking_id` | String | 예매 번호 | `"BK20260128001"` |

### completion_status 값

| 상태 | 설명 | 발생 시점 |
|------|------|----------|
| `success` | 결제 완료 | `/api/complete` 호출 시 |
| `failed_seat_taken` | 이선좌로 실패 | 좌석 선택 중 이선좌 발생 |
| `failed_timeout` | 시간 초과 | 타이머 만료 |
| `failed_abandoned` | 중간 이탈 | `beforeunload` 이벤트 |

### Stages 구조

각 단계는 다음 공통 필드를 가짐:

```json
{
  "entry_time": "2026-01-28T12:00:00Z",
  "exit_time": "2026-01-28T12:00:15Z",
  "duration_ms": 15000,
  // ... 단계별 고유 데이터
}
```

**단계별 고유 데이터**:
- `perf`: `card_clicks`, `date_selections`, `time_selections`, `actions`, `mouse_trajectory`
- `queue`: `initial_position`, `final_position`, `position_updates`, `wait_duration_ms`, `mouse_trajectory`
- `captcha`: `attempts`, `time_to_solve_ms`
- `section`: `final_section`, `final_grade`, `clicks`, `mouse_trajectory`
- `seat`: `selected_seats`, `clicks`, `hovers`, `seat_taken_events`, `mouse_trajectory`
- `discount`: `selected_discount`
- `order_info`: `delivery_type`
- `payment`: `payment_type`, `captcha_attempts`, `completed`, `completed_time`

---

## 📁 파일명 형식

```
[YYYYMMDD]_[performance_id]_[flow_id]_[status].json
```

### 예시

```
20260128_perf001_flow_abc123_success.json
20260128_perf001_flow_xyz789_failed_seat_taken.json
20260128_perf002_flow_def456_failed_abandoned.json
20260128_perf001_flow_qwe321_failed_timeout.json
```

### 장점

1. **정렬 용이**: 날짜순 정렬 자동
2. **필터링 용이**: 공연별, 상태별 필터링 쉬움
3. **고유성 보장**: flow_id 포함으로 중복 없음
4. **가독성**: 파일명만 봐도 내용 파악 가능

---

## 🔧 구현 계획

### 1. `log_collector.js` 수정

#### 새로운 함수 추가

**`initFlowLog()`** - Flow 초기화
```javascript
initFlowLog: function(perfId, perfTitle, selectedDate, selectedTime, userId, userEmail) {
  const flowId = 'flow_' + 
    new Date().toISOString().split('T')[0].replace(/-/g, '') + 
    '_' + Math.random().toString(36).substr(2, 6);
  
  const flowLog = {
    metadata: {
      flow_id: flowId,
      session_id: 'sess_' + Math.random().toString(36).substr(2, 8),
      user_id: userId,
      user_email: userEmail,
      user_ip: null,  // 서버에서 설정
      created_at: new Date().toISOString(),
      
      performance_id: perfId,
      performance_title: perfTitle,
      selected_date: selectedDate,
      selected_time: selectedTime,
      
      flow_start_time: new Date().toISOString(),
      flow_end_time: null,
      total_duration_ms: null,
      
      is_completed: false,
      completion_status: null,
      final_seats: null,
      booking_id: null,
      
      browser_info: this.initBrowserInfo()
    },
    stages: {}
  };
  
  sessionStorage.setItem('flowLogData', JSON.stringify(flowLog));
  return flowLog;
}
```

**`addStageToFlow()`** - 단계 데이터 추가
```javascript
addStageToFlow: function(stageName, stageData) {
  const flowLog = JSON.parse(sessionStorage.getItem('flowLogData') || '{}');
  if (!flowLog.metadata) return;
  
  flowLog.stages[stageName] = {
    entry_time: new Date().toISOString(),
    ...stageData
  };
  
  sessionStorage.setItem('flowLogData', JSON.stringify(flowLog));
}
```

**`completeFlow()`** - Flow 완료 처리
```javascript
completeFlow: function(status, finalSeats, bookingId) {
  const flowLog = JSON.parse(sessionStorage.getItem('flowLogData') || '{}');
  if (!flowLog.metadata) return null;
  
  const now = new Date();
  flowLog.metadata.flow_end_time = now.toISOString();
  flowLog.metadata.total_duration_ms = now - new Date(flowLog.metadata.flow_start_time);
  flowLog.metadata.is_completed = (status === 'success');
  flowLog.metadata.completion_status = status;
  flowLog.metadata.final_seats = finalSeats;
  flowLog.metadata.booking_id = bookingId;
  
  return flowLog;
}
```

**`sendFlowLog()`** - 서버 전송
```javascript
sendFlowLog: async function(flowLog) {
  try {
    const response = await fetch('/api/flow-log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(flowLog)
    });
    
    sessionStorage.removeItem('flowLogData');
    return response;
  } catch (error) {
    console.error('Failed to send flow log:', error);
    throw error;
  }
}
```

### 2. 페이지별 JS 파일 수정

#### `perf_list.js` - Flow 시작

**수정 위치**: `goToQueue()` 함수

```javascript
function goToQueue() {
  // 1. Flow 로그 초기화
  const perf = performances.find(p => p.id === currentPerfId);
  const flowLog = LogCollector.initFlowLog(
    currentPerfId,
    perf.title,
    selectedDate,
    selectedTime,
    typeof userId !== 'undefined' ? userId : '',
    typeof userEmail !== 'undefined' ? userEmail : ''
  );
  
  // 2. perf 단계 데이터 추가
  LogCollector.addStageToFlow('perf', {
    exit_time: new Date().toISOString(),
    duration_ms: Date.now() - new Date(logData.page_entry_time).getTime(),
    card_clicks: logData.card_clicks,
    date_selections: logData.date_selections,
    time_selections: logData.time_selections,
    actions: logData.actions,
    mouse_trajectory: logData.mouse_trajectory
  });
  
  // 3. 다음 페이지로 이동
  window.location.href = `/queue/${currentPerfId}?date=${selectedDate}&time=${selectedTime}`;
}
```

#### `queue.js` - queue 단계 추가

**수정 위치**: `enterBooking()` 함수

```javascript
function enterBooking() {
  // queue 단계 데이터 추가
  LogCollector.addStageToFlow('queue', {
    exit_time: new Date().toISOString(),
    duration_ms: Date.now() - startTime,
    initial_position: logData.initial_position,
    final_position: 0,
    total_queue: logData.total_queue,
    wait_duration_ms: logData.wait_duration_ms,
    position_updates: logData.position_updates,
    mouse_trajectory: logData.mouse_trajectory
  });
  
  // 다음 페이지로 이동
  const pId = typeof perfId !== 'undefined' ? perfId : '';
  const sDate = typeof selectedDate !== 'undefined' ? selectedDate : '';
  const sTime = typeof selectedTime !== 'undefined' ? selectedTime : '';
  window.location.href = `/captcha/${pId}?date=${sDate}&time=${sTime}`;
}
```

#### `captcha.js` - captcha 단계 추가

**새로 추가**: captcha에는 현재 로그 수집이 없으므로 추가 필요

```javascript
// 페이지 진입 시
const captchaStartTime = Date.now();
let attemptCount = 0;

// 성공 시
function verifyCaptcha() {
  // ... 기존 검증 로직
  
  if (input === captchaCode) {
    // captcha 단계 데이터 추가
    LogCollector.addStageToFlow('captcha', {
      exit_time: new Date().toISOString(),
      duration_ms: Date.now() - captchaStartTime,
      attempts: attemptCount,
      time_to_solve_ms: Date.now() - captchaStartTime
    });
    
    // 다음 페이지로 이동
    window.location.href = `/section/${pId}?date=${sDate}&time=${sTime}`;
  }
}
```

#### `section_select.js` - section 단계 추가

**수정 위치**: `goToSeats()` 함수

```javascript
function goToSeats() {
  if (!selectedSection) return;
  
  // section 단계 데이터 추가
  LogCollector.addStageToFlow('section', {
    exit_time: new Date().toISOString(),
    duration_ms: Date.now() - pageStartTime,
    final_section: selectedSection,
    final_grade: selectedGrade,
    clicks: sectionClicks,
    mouse_trajectory: mouseTrajectory
  });
  
  // 다음 페이지로 이동
  const pId = typeof perfId !== 'undefined' ? perfId : '';
  const sDate = typeof selectedDate !== 'undefined' ? selectedDate : '';
  const sTime = typeof selectedTime !== 'undefined' ? selectedTime : '';
  window.location.href = `/booking/${pId}?date=${sDate}&time=${sTime}&section=${selectedSection}&grade=${selectedGrade}`;
}
```

#### `seat_select.js` - seat 단계 추가

**수정 위치**: `goToCheckout()` 함수

```javascript
function goToCheckout() {
  // seat 단계 데이터 추가
  LogCollector.addStageToFlow('seat', {
    exit_time: new Date().toISOString(),
    duration_ms: Date.now() - pageStartTime,
    selected_seats: selectedSeats,
    section: selectedSection,
    grade: selectedGrade,
    clicks: clicks,
    hovers: hovers,
    seat_taken_events: [],  // 이선좌 발생 시 추가
    mouse_trajectory: mouseTrajectory
  });
  
  // 다음 페이지로 이동
  const seatsParam = selectedSeats.join(',');
  window.location.href = `/step2/${perfId}?date=${selectedDate}&time=${selectedTime}&seats=${seatsParam}`;
}
```

#### `discount_select.js` - discount 단계 추가

**수정 위치**: `goNext()` 함수

```javascript
function goNext() {
  // discount 단계 데이터 추가
  LogCollector.addStageToFlow('discount', {
    exit_time: new Date().toISOString(),
    duration_ms: Date.now() - pageStartTime,
    selected_discount: selectedDiscount
  });
  
  // 다음 페이지로 이동
  const pId = typeof perfId !== 'undefined' ? perfId : '';
  const sDate = typeof selectedDate !== 'undefined' ? selectedDate : '';
  const sTime = typeof selectedTime !== 'undefined' ? selectedTime : '';
  const seats = typeof selectedSeats !== 'undefined' ? selectedSeats : '';
  window.location.href = `/step3/${pId}?date=${sDate}&time=${sTime}&seats=${seats}&discount=${selectedDiscount}`;
}
```

#### `order_info.js` - order_info 단계 추가

**수정 위치**: `goNext()` 함수

```javascript
function goNext() {
  // order_info 단계 데이터 추가
  LogCollector.addStageToFlow('order_info', {
    exit_time: new Date().toISOString(),
    duration_ms: Date.now() - pageStartTime,
    delivery_type: selectedDelivery
  });
  
  // 다음 페이지로 이동
  const pId = typeof perfId !== 'undefined' ? perfId : '';
  const sDate = typeof selectedDate !== 'undefined' ? selectedDate : '';
  const sTime = typeof selectedTime !== 'undefined' ? selectedTime : '';
  const seats = typeof selectedSeats !== 'undefined' ? selectedSeats : '';
  const discount = typeof discountType !== 'undefined' ? discountType : 'normal';
  window.location.href = `/step4/${pId}?date=${sDate}&time=${sTime}&seats=${seats}&discount=${discount}&delivery=${selectedDelivery}`;
}
```

#### `payment.js` - payment 단계 추가 및 Flow 완료

**수정 위치**: `completeBooking()` 함수

```javascript
async function completeBooking() {
  // payment 단계 데이터 추가
  LogCollector.addStageToFlow('payment', {
    exit_time: new Date().toISOString(),
    duration_ms: Date.now() - pageStartTime,
    payment_type: selectedPayment,
    captcha_attempts: 2,
    completed: true,
    completed_time: new Date().toISOString()
  });
  
  // 예매 완료 API 호출
  const sId = typeof sessionId !== 'undefined' ? sessionId : '';
  const seats = typeof selectedSeats !== 'undefined' ? selectedSeats : [];
  const discount = typeof discountType !== 'undefined' ? discountType : 'normal';
  const delivery = typeof deliveryType !== 'undefined' ? deliveryType : 'pickup';
  
  const sessionData = {
    session_id: sId,
    page: 'step4_payment',
    selected_seats: seats,
    discount_type: discount,
    delivery_type: delivery,
    payment_type: selectedPayment
  };
  
  const result = await fetch('/api/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sessionData)
  }).then(r => r.json());
  
  if (result.success) {
    // Flow 완료 처리
    const flowLog = LogCollector.completeFlow(
      'success',
      seats,
      result.booking_id
    );
    
    // 서버로 전송
    await LogCollector.sendFlowLog(flowLog);
    
    // 완료 모달 표시
    document.getElementById('bookingId').textContent = '예매번호: ' + result.booking_id;
    document.getElementById('completeModal').classList.add('active');
  }
}
```

### 3. 이탈 감지 (`beforeunload`)

**모든 페이지에 공통 적용** (queue부터 payment까지):

```javascript
// DOM 로드 후
document.addEventListener('DOMContentLoaded', function() {
  // beforeunload 이벤트로 이탈 감지
  window.addEventListener('beforeunload', function(e) {
    const flowLog = LogCollector.completeFlow(
      'failed_abandoned',
      null,
      null
    );
    
    if (flowLog) {
      // sendBeacon으로 바로 전송 (비동기 X)
      navigator.sendBeacon('/api/flow-log', JSON.stringify(flowLog));
    }
  });
});
```

### 4. 서버 API 수정 (`main.py`)

#### 새로운 엔드포인트 추가

```python
@app.post("/api/flow-log")
async def save_flow_log(request: Request, data: dict):
    """Flow 로그 저장"""
    try:
        client_ip = request.client.host
        
        # IP 주소 추가
        data['metadata']['user_ip'] = client_ip
        
        # 파일명 생성
        flow_id = data['metadata']['flow_id']
        perf_id = data['metadata']['performance_id']
        status = data['metadata']['completion_status']
        created_at = data['metadata']['created_at']
        date = created_at[:10].replace('-', '')  # YYYYMMDD
        
        filename = f"{date}_{perf_id}_{flow_id}_{status}.json"
        filepath = os.path.join(LOGS_DIR, filename)
        
        # 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Flow log saved: {filename}")
        return {"success": True, "flow_id": flow_id, "filename": filename}
    
    except Exception as e:
        print(f"Failed to save flow log: {e}")
        return {"success": False, "error": str(e)}
```

#### 기존 엔드포인트 제거 또는 보존

**제거 예정**:
- `/api/stage-log` - flow-log로 대체
- `/api/session-log` - flow-log로 대체

**보존**:
- `/api/complete` - 예매 완료 처리 (비즈니스 로직)
- `/api/log` - 실시간 행동 로그 (필요 시)

---

## 🧪 테스트 계획

### 1. 정상 플로우 테스트

**시나리오**: 공연 선택 → 예매 완료

**검증 항목**:
- [ ] flow_id가 공연 선택 시 생성되는가?
- [ ] 각 단계마다 `stages`에 데이터가 추가되는가?
- [ ] 결제 완료 시 `completion_status: "success"`인가?
- [ ] 파일명이 `20260128_perf001_flow_xxx_success.json` 형식인가?
- [ ] JSON 구조가 올바른가?

### 2. 이선좌 플로우 테스트

**시나리오**: 좌석 선택 중 이선좌 → 처음부터 재시도

**검증 항목**:
- [ ] 첫 번째 flow는 `failed_seat_taken`으로 저장되는가?
- [ ] 재시도 시 새로운 flow_id가 생성되는가?
- [ ] 두 개의 별도 JSON 파일이 생성되는가?

### 3. 이탈 플로우 테스트

**시나리오**: 중간에 브라우저 닫기

**검증 항목**:
- [ ] `beforeunload` 이벤트가 발생하는가?
- [ ] `completion_status: "failed_abandoned"`로 저장되는가?
- [ ] `sendBeacon`으로 정상 전송되는가?

### 4. 타임아웃 플로우 테스트

**시나리오**: 타이머 만료

**검증 항목**:
- [ ] `completion_status: "failed_timeout"`으로 저장되는가?
- [ ] 해당 시점까지의 데이터가 모두 포함되는가?

---

## 📊 데이터 분석 예시

### Flow 성공률 분석

```python
import json
import os

success_count = 0
total_count = 0

for filename in os.listdir('logs/'):
    if filename.endswith('.json'):
        total_count += 1
        if 'success' in filename:
            success_count += 1

success_rate = success_count / total_count * 100
print(f"예매 성공률: {success_rate:.2f}%")
```

### 평균 소요 시간 분석

```python
durations = []

for filename in os.listdir('logs/'):
    if filename.endswith('_success.json'):
        with open(f'logs/{filename}', 'r') as f:
            data = json.load(f)
            durations.append(data['metadata']['total_duration_ms'])

avg_duration = sum(durations) / len(durations)
print(f"평균 예매 소요 시간: {avg_duration / 1000:.2f}초")
```

### 단계별 이탈률 분석

```python
stage_counts = {}

for filename in os.listdir('logs/'):
    if 'failed' in filename:
        with open(f'logs/{filename}', 'r') as f:
            data = json.load(f)
            last_stage = list(data['stages'].keys())[-1]
            stage_counts[last_stage] = stage_counts.get(last_stage, 0) + 1

print("단계별 이탈 현황:")
for stage, count in sorted(stage_counts.items()):
    print(f"  {stage}: {count}회")
```

---

## ✅ 구현 체크리스트

### 코드 수정
- [ ] `log_collector.js`에 flow 관련 함수 추가
  - [ ] `initFlowLog()`
  - [ ] `addStageToFlow()`
  - [ ] `completeFlow()`
  - [ ] `sendFlowLog()`
- [ ] `perf_list.js` - flow 초기화 및 perf 단계 추가
- [ ] `queue.js` - queue 단계 추가
- [ ] `captcha.js` - captcha 단계 추가 (새로 작성)
- [ ] `section_select.js` - section 단계 추가
- [ ] `seat_select.js` - seat 단계 추가
- [ ] `discount_select.js` - discount 단계 추가
- [ ] `order_info.js` - order_info 단계 추가
- [ ] `payment.js` - payment 단계 추가 및 flow 완료
- [ ] 모든 페이지에 `beforeunload` 이탈 감지 추가

### 서버 수정
- [ ] `main.py`에 `/api/flow-log` 엔드포인트 추가
- [ ] 기존 `/api/stage-log`, `/api/session-log` 제거 또는 주석 처리
- [ ] 파일명 생성 로직 구현
- [ ] IP 주소 자동 추가 로직 구현

### 테스트
- [ ] 정상 플로우 (성공) 테스트
- [ ] 이선좌 플로우 테스트
- [ ] 이탈 플로우 테스트
- [ ] 타임아웃 플로우 테스트
- [ ] 파일명 형식 검증
- [ ] JSON 구조 검증
- [ ] 브라우저 콘솔 에러 확인

### 문서화
- [ ] `log_describe.md` 업데이트 (flow 기반 설명)
- [ ] `log_user.md` 업데이트 (flow 기반 사용자 여정)
- [ ] 주석 추가 (모든 새로운 함수)

---

## 🎯 기대 효과

### 1. 데이터 분석 용이성 ↑
- 하나의 예매 시도 = 하나의 JSON
- 전체 과정을 한 눈에 파악 가능

### 2. ML 학습 효율성 ↑
- 명확한 학습 단위 (flow_id)
- 라벨링 간편 (success/failed)

### 3. 봇 탐지 정확도 ↑
- 전체 과정의 패턴 분석 가능
- 단계별 비정상 행동 누적 분석

### 4. 유지보수성 ↑
- 로그 구조가 명확하고 일관됨
- 파일 관리 용이 (날짜_공연_flow_상태)

---

## 🚀 진행 순서

1. **log_collector.js 수정** (핵심 함수 구현)
2. **perf_list.js 수정** (flow 시작점)
3. **나머지 페이지 순차적 수정**
4. **서버 API 구현**
5. **테스트**
6. **문서 업데이트**

준비되면 알려주세요! 🎉
