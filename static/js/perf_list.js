// 공연 목록 페이지 JavaScript
// 템플릿에서 performances 변수를 전역으로 설정해야 함

// ============== LogCollector 사용 ==============
// 로그 데이터 초기화
const logData = LogCollector.initPerfListLog();

let currentPerfId = null;
let selectedDate = null;
let selectedTime = null;

function openModal(perfId) {
  currentPerfId = perfId;
  logData.performance_id = perfId;

  // performances는 템플릿에서 전역으로 설정됨
  const perf = performances.find(p => p.id === perfId);

  // 카드 클릭 로그
  logData.card_clicks.push({
    performance_id: perfId,
    performance_title: perf.title,
    timestamp: new Date().toISOString()
  });
  logData.actions.push({
    action: 'card_click',
    target: perfId,
    timestamp: new Date().toISOString()
  });

  document.getElementById('modalTitle').textContent = perf.title;

  // 날짜 옵션
  const dateContainer = document.getElementById('dateOptions');
  dateContainer.innerHTML = perf.dates.map(d =>
    `<div class="date-option" onclick="selectDate(this, '${d}')">${d}</div>`
  ).join('');

  // 시간 옵션
  const timeContainer = document.getElementById('timeOptions');
  timeContainer.innerHTML = perf.times.map(t =>
    `<div class="time-option" onclick="selectTime(this, '${t}')">${t}</div>`
  ).join('');

  selectedDate = null;
  selectedTime = null;
  document.getElementById('btnConfirm').disabled = true;

  document.getElementById('modalOverlay').classList.add('active');
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('active');
  logData.actions.push({
    action: 'modal_close',
    timestamp: new Date().toISOString()
  });
}

function selectDate(el, date) {
  document.querySelectorAll('.date-option').forEach(e => e.classList.remove('selected'));
  el.classList.add('selected');
  selectedDate = date;

  logData.date_selections.push({
    date: date,
    timestamp: new Date().toISOString()
  });
  logData.actions.push({
    action: 'date_select',
    target: date,
    timestamp: new Date().toISOString()
  });

  checkSelection();
}

function selectTime(el, time) {
  document.querySelectorAll('.time-option').forEach(e => e.classList.remove('selected'));
  el.classList.add('selected');
  selectedTime = time;

  logData.time_selections.push({
    time: time,
    timestamp: new Date().toISOString()
  });
  logData.actions.push({
    action: 'time_select',
    target: time,
    timestamp: new Date().toISOString()
  });

  checkSelection();
}

function checkSelection() {
  document.getElementById('btnConfirm').disabled = !(selectedDate && selectedTime);
}

function goToQueue() {
  logData.page_exit_time = new Date().toISOString();
  logData.selected_date = selectedDate;
  logData.selected_time = selectedTime;
  logData.actions.push({
    action: 'booking_start',
    target: currentPerfId,
    date: selectedDate,
    time: selectedTime,
    timestamp: new Date().toISOString()
  });

  // LogCollector 사용하여 로그 저장 후 페이지 이동
  LogCollector.sendStageLog(logData).then(() => {
    window.location.href = `/queue/${currentPerfId}?date=${selectedDate}&time=${selectedTime}`;
  }).catch(() => {
    window.location.href = `/queue/${currentPerfId}?date=${selectedDate}&time=${selectedTime}`;
  });
}

// 모달 외부 클릭 시 닫기
document.addEventListener('DOMContentLoaded', function () {
  const modalOverlay = document.getElementById('modalOverlay');
  if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === e.currentTarget) closeModal();
    });
  }
});
