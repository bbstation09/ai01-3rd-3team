// 구역 선택 페이지 JavaScript
// 템플릿에서 perfId, selectedDate, selectedTime, performance.price 변수를 전역으로 설정해야 함

let selectedSection = null;
let selectedGrade = null;
let selectedPrice = 0;
const pageStartTime = Date.now();
let mouseTrajectory = [];
let sectionClicks = [];

// ============== LogCollector 사용 ==============
// 예매창 로그 시작 (구역선택 ~ 할인권종 진입까지)
const bookLogData = LogCollector.initBookLog(
  typeof perfId !== 'undefined' ? perfId : '',
  typeof selectedDate !== 'undefined' ? selectedDate : '',
  typeof selectedTime !== 'undefined' ? selectedTime : ''
);

function saveBookLogToStorage() {
  LogCollector.saveBookLog(bookLogData);
}

// 마우스 궤적 수집
let lastMouseTime = 0;
document.addEventListener('mousemove', (e) => {
  const now = Date.now();
  if (now - lastMouseTime >= 30) {
    mouseTrajectory.push({
      x: e.clientX,
      y: e.clientY,
      nx: e.clientX / window.innerWidth,
      ny: e.clientY / window.innerHeight,
      t: now - pageStartTime
    });
    lastMouseTime = now;
  }
});

function selectSection(e, el, sectionId, grade, price) {
  // 기존 선택 해제
  document.querySelectorAll('.section-box').forEach(box => box.classList.remove('selected'));

  // 새로운 선택
  el.classList.add('selected');
  selectedSection = sectionId;
  selectedGrade = grade;
  selectedPrice = price;

  // 실제 마우스 클릭 좌표 사용
  const clickX = e.clientX;
  const clickY = e.clientY;

  // 마우스 궤적에도 클릭 좌표 추가 (궤적-클릭 연결)
  mouseTrajectory.push({
    x: clickX,
    y: clickY,
    nx: clickX / window.innerWidth,
    ny: clickY / window.innerHeight,
    t: Date.now() - pageStartTime
  });

  // 로그 기록
  sectionClicks.push({
    section: sectionId,
    grade: grade,
    price: price,
    x: clickX,
    y: clickY,
    nx: clickX / window.innerWidth,
    ny: clickY / window.innerHeight,
    viewport: { w: window.innerWidth, h: window.innerHeight },
    timestamp: new Date().toISOString()
  });

  if (bookLogData) {
    bookLogData.section_selection.clicks.push({
      section: sectionId,
      x: Math.round(clickX),
      y: Math.round(clickY),
      nx: clickX / window.innerWidth,
      ny: clickY / window.innerHeight,
      viewport: { w: window.innerWidth, h: window.innerHeight },
      timestamp: new Date().toISOString()
    });
    LogCollector.saveBookLog(bookLogData);
  }

  // UI 업데이트
  const sectionNames = {
    'VIP-L': 'VIP구역 좌', 'VIP-C': 'VIP구역 중앙', 'VIP-R': 'VIP구역 우',
    'R-L': 'R구역 좌', 'R-C': 'R구역 중앙', 'R-R': 'R구역 우',
    'S-L': 'S구역 좌', 'S-R': 'S구역 우'
  };

  document.getElementById('selectedSectionName').textContent = sectionNames[sectionId];
  document.getElementById('selectedGrade').textContent = grade + '석';
  document.getElementById('selectedPrice').textContent = price.toLocaleString() + '원';

  const btn = document.getElementById('btnNext');
  btn.disabled = false;
  btn.textContent = '좌석 선택하기 →';
}

function goToSeats() {
  if (!selectedSection) return;

  const pId = typeof perfId !== 'undefined' ? perfId : '';
  const sDate = typeof selectedDate !== 'undefined' ? selectedDate : '';
  const sTime = typeof selectedTime !== 'undefined' ? selectedTime : '';

  // section 단계 데이터 추가
  const sectionStageData = {
    exit_time: new Date().toISOString(),
    duration_ms: Date.now() - pageStartTime,
    final_section: selectedSection,
    final_grade: selectedGrade,
    clicks: sectionClicks,
    mouse_trajectory: mouseTrajectory
  };

  LogCollector.addStageToFlow('section', sectionStageData);

  // 다음 페이지로 이동
  window.location.href = `/booking/${pId}?date=${sDate}&time=${sTime}&section=${selectedSection}&grade=${selectedGrade}`;
}

// 타이머
let timeLeft = 300;
function updateTimer() {
  const m = Math.floor(timeLeft / 60);
  const s = timeLeft % 60;
  document.getElementById('timer').textContent = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;

  if (timeLeft > 0) {
    timeLeft--;
    setTimeout(updateTimer, 1000);
  } else {
    alert('시간이 초과되었습니다. 다시 시도해주세요.');
    location.href = '/performances';
  }
}

// DOM 로드 후 초기화
document.addEventListener('DOMContentLoaded', function () {
  updateTimer();
  LogCollector.initMouseTracking(mouseTrajectory, 50, Date.now(), true);

  // 이탈 감지
  window.addEventListener('beforeunload', function () {
    const flowLog = LogCollector.completeFlow('failed_abandoned', null, null);
    if (flowLog) {
      navigator.sendBeacon('/api/flow-log', JSON.stringify(flowLog));
    }
  });
});
