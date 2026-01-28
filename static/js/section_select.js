// 구역 선택 페이지 JavaScript
// 템플릿에서 perfId, selectedDate, selectedTime, performance.price 변수를 전역으로 설정해야 함

let selectedSection = null;
let selectedGrade = null;
let selectedPrice = 0;
const pageStartTime = Date.now();
let mouseTrajectory = [];
let sectionClicks = [];

// 예매창 로그 시작 (구역선택 ~ 할인권종 진입까지)
const bookSessionId = 'book_' + Math.random().toString(36).substr(2, 8);

// 브라우저/OS 정보 수집 (Headless Chrome, 봇 탐지용)
const browserInfo = {
  userAgent: navigator.userAgent,
  platform: navigator.platform,
  cookieEnabled: navigator.cookieEnabled,
  doNotTrack: navigator.doNotTrack,
  hardwareConcurrency: navigator.hardwareConcurrency,
  deviceMemory: navigator.deviceMemory,
  maxTouchPoints: navigator.maxTouchPoints,
  webdriver: navigator.webdriver,  // Headless Chrome 탐지
  screen: {
    width: screen.width,
    height: screen.height,
    colorDepth: screen.colorDepth,
    pixelRatio: window.devicePixelRatio
  },
  window: {
    outerWidth: window.outerWidth,
    outerHeight: window.outerHeight
  },
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
};

const bookLogData = {
  session_id: bookSessionId,
  stage: 'book',
  performance_id: typeof perfId !== 'undefined' ? perfId : '',
  selected_date: typeof selectedDate !== 'undefined' ? selectedDate : '',
  selected_time: typeof selectedTime !== 'undefined' ? selectedTime : '',
  booking_start_time: new Date().toISOString(),
  viewport: { w: window.innerWidth, h: window.innerHeight },
  browser_info: browserInfo,
  section_selection: {
    start_time: new Date().toISOString(),
    clicks: [],
    final_section: null,
    final_grade: null,
    end_time: null,
    mouse_trajectory: []
  },
  seat_selection: null,
  discount: null,
  booking_end_time: null
};

function saveBookLogToStorage() {
  sessionStorage.setItem('bookLogData', JSON.stringify(bookLogData));
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
    sessionStorage.setItem('bookLogData', JSON.stringify(bookLogData));
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

  if (bookLogData) {
    bookLogData.section_selection.end_time = new Date().toISOString();
    bookLogData.section_selection.final_section = selectedSection;
    bookLogData.section_selection.final_grade = selectedGrade;
    bookLogData.section_selection.mouse_trajectory = mouseTrajectory;
    sessionStorage.setItem('bookLogData', JSON.stringify(bookLogData));
  }

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
  saveBookLogToStorage();
  updateTimer();
});
