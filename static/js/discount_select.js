// 할인권종 선택 페이지(step2_discount) JavaScript
// 템플릿에서 perfId, selectedDate, selectedTime, selectedSeats 변수를 전역으로 설정해야 함

let selectedDiscount = 'normal';
let pageStartTime = Date.now();

// 페이지 진입 시 book 로그 서버 전송 (로그 수집 종료 시점)
async function sendBookLog() {
  let bookLogData = null;
  try {
    bookLogData = JSON.parse(sessionStorage.getItem('bookLogData'));
  } catch (e) { }

  if (bookLogData) {
    bookLogData.booking_end_time = new Date().toISOString();
    bookLogData.discount = {
      page_entry_time: new Date().toISOString()
    };

    // 서버로 로그 전송
    try {
      await fetch('/api/stage-log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookLogData)
      });
      console.log('Book log sent successfully');
    } catch (e) {
      console.error('Failed to send book log:', e);
    }

    // sessionStorage 정리
    sessionStorage.removeItem('bookLogData');
  }
}

function selectDiscount(el, type) {
  document.querySelectorAll('.discount-option').forEach(e => e.classList.remove('selected'));
  el.classList.add('selected');
  el.querySelector('input').checked = true;
  selectedDiscount = type;
}

function goNext() {
  const pId = typeof perfId !== 'undefined' ? perfId : '';
  const sDate = typeof selectedDate !== 'undefined' ? selectedDate : '';
  const sTime = typeof selectedTime !== 'undefined' ? selectedTime : '';
  const seats = typeof selectedSeats !== 'undefined' ? selectedSeats : '';

  window.location.href = `/step3/${pId}?date=${sDate}&time=${sTime}&seats=${seats}&discount=${selectedDiscount}`;
}

// 타이머
let timeLeft = 300;
function updateTimer() {
  const m = Math.floor(timeLeft / 60), s = timeLeft % 60;
  document.getElementById('timer').textContent = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  if (timeLeft-- > 0) setTimeout(updateTimer, 1000);
  else { alert('시간 초과'); location.href = '/performances'; }
}

// DOM 로드 후 초기화
document.addEventListener('DOMContentLoaded', function () {
  sendBookLog();
  updateTimer();
});
