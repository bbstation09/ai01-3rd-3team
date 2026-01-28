// 대기열 페이지 JavaScript

// 페이지 초기화 시 호출 필요 (template에서 전역변수 설정 필요)
// const perfId, selectedDate, selectedTime, totalQueue, initialPosition

let isReady = false;

// 대기열 로그 데이터
const sessionId = 'que_' + Math.random().toString(36).substr(2, 8);
const logData = {
  session_id: sessionId,
  stage: 'que',
  performance_id: typeof perfId !== 'undefined' ? perfId : '',
  selected_date: typeof selectedDate !== 'undefined' ? selectedDate : '',
  selected_time: typeof selectedTime !== 'undefined' ? selectedTime : '',
  queue_start_time: new Date().toISOString(),
  initial_position: typeof initialPosition !== 'undefined' ? initialPosition : 0,
  total_queue: typeof totalQueue !== 'undefined' ? totalQueue : 0,
  position_updates: [],
  queue_end_time: null,
  final_position: null,
  wait_duration_ms: null,
  mouse_trajectory: []
};
const startTime = Date.now();

// 마우스 궤적 수집
let lastMouseTime = 0;
document.addEventListener('mousemove', (e) => {
  const now = Date.now();
  if (now - lastMouseTime >= 30) {
    logData.mouse_trajectory.push({
      x: e.clientX,
      y: e.clientY,
      t: now - startTime
    });
    lastMouseTime = now;
  }
});

function updateQueue() {
  fetch('/api/queue/status')
    .then(res => res.json())
    .then(data => {
      if (data.status === 'ready') {
        isReady = true;

        // 로그 기록
        logData.queue_end_time = new Date().toISOString();
        logData.final_position = 0;
        logData.wait_duration_ms = Date.now() - startTime;
        logData.position_updates.push({
          position: 0,
          status: 'ready',
          timestamp: new Date().toISOString()
        });

        document.getElementById('position').textContent = '0';
        document.getElementById('progressFill').style.width = '100%';
        document.getElementById('progressPercent').textContent = '100%';
        document.getElementById('estimatedTime').textContent = '입장 가능!';
        document.getElementById('loadingDots').style.display = 'none';

        // 자동 입장 (버튼 없이)
        setTimeout(() => {
          enterBooking();
        }, 800);
      } else if (data.status === 'waiting') {
        const position = data.position;
        const total = typeof totalQueue !== 'undefined' ? totalQueue : 100;
        const progress = Math.round((1 - position / total) * 100);

        // 위치 변화 로그
        logData.position_updates.push({
          position: position,
          progress: progress,
          estimated_minutes: data.estimated_minutes,
          timestamp: new Date().toISOString()
        });

        document.getElementById('position').textContent = position.toLocaleString();
        document.getElementById('progressFill').style.width = progress + '%';
        document.getElementById('progressPercent').textContent = progress + '%';
        document.getElementById('estimatedTime').textContent = `약 ${data.estimated_minutes}분`;
      }
    })
    .catch(err => console.error('Error:', err));
}

function enterBooking() {
  logData.entry_time = new Date().toISOString();

  const pId = typeof perfId !== 'undefined' ? perfId : '';
  const sDate = typeof selectedDate !== 'undefined' ? selectedDate : '';
  const sTime = typeof selectedTime !== 'undefined' ? selectedTime : '';

  // 로그 저장 후 페이지 이동
  fetch('/api/stage-log', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(logData)
  }).then(() => {
    window.location.href = `/captcha/${pId}?date=${sDate}&time=${sTime}`;
  }).catch(() => {
    window.location.href = `/captcha/${pId}?date=${sDate}&time=${sTime}`;
  });
}

// 1초마다 대기열 업데이트
setInterval(updateQueue, 1000);

// DOM 로드 후 초기화
document.addEventListener('DOMContentLoaded', function () {
  updateQueue();
});
