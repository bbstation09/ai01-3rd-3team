// 결제 페이지(step4_payment) JavaScript
// 템플릿에서 sessionId, perfId, selectedSeats, discountType, deliveryType 변수 설정 필요

let selectedPayment = 'card';
let captchaCode = '';
let captchaStartTime = 0;

function selectPayment(el, type) {
  document.querySelectorAll('.payment-option').forEach(e => e.classList.remove('selected'));
  el.classList.add('selected');
  el.querySelector('input').checked = true;
  selectedPayment = type;
}

function showCaptcha() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  captchaCode = '';
  for (let i = 0; i < 6; i++) captchaCode += chars[Math.floor(Math.random() * chars.length)];
  document.getElementById('captchaText').textContent = captchaCode;
  document.getElementById('captchaInput').value = '';
  document.getElementById('captchaError').style.display = 'none';
  document.getElementById('captchaModal').classList.add('active');
  captchaStartTime = Date.now();
  document.getElementById('captchaInput').focus();
}

function verifyCaptcha() {
  const input = document.getElementById('captchaInput').value.toUpperCase();

  if (input === captchaCode) {
    document.getElementById('captchaModal').classList.remove('active');
    completeBooking();
  } else {
    document.getElementById('captchaError').style.display = 'block';
    document.getElementById('captchaInput').value = '';
    document.getElementById('captchaInput').focus();
  }
}

async function completeBooking() {
  // book 로그의 session_id 가져오기
  let bookSessionId = '';
  try {
    const bookLogData = JSON.parse(sessionStorage.getItem('bookLogData'));
    if (bookLogData && bookLogData.session_id) {
      bookSessionId = bookLogData.session_id;
    }
  } catch (e) { }

  const sId = typeof sessionId !== 'undefined' ? sessionId : '';
  const seats = typeof selectedSeats !== 'undefined' ? selectedSeats : [];
  const discount = typeof discountType !== 'undefined' ? discountType : 'normal';
  const delivery = typeof deliveryType !== 'undefined' ? deliveryType : 'pickup';

  // 예매 완료 API 호출
  const sessionData = {
    session_id: bookSessionId || sId,
    page: 'step4_payment',
    selected_seats: seats,
    discount_type: discount,
    delivery_type: delivery,
    payment_type: selectedPayment
  };

  const response = await fetch('/api/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sessionData)
  });

  const result = await response.json();
  if (result.success) {
    // sessionStorage 정리
    sessionStorage.removeItem('bookLogData');
    document.getElementById('bookingId').textContent = '예매번호: ' + result.booking_id;
    document.getElementById('completeModal').classList.add('active');
  }
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
  updateTimer();
});
