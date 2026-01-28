/**
 * 로그 수집 중앙 관리 라이브러리
 * 각 페이지에서 사용하는 로그 수집 기능을 통합 관리
 */
const LogCollector = {

  // ============== 공통 유틸리티 ==============

  /**
   * 세션 ID 생성
   * @param {string} prefix - 접두사 (예: 'perf', 'que', 'book')
   * @returns {string} 생성된 세션 ID
   * from: perf_list.js, queue.js, section_select.js
   */
  generateSessionId: function (prefix) {
    return prefix + '_' + Math.random().toString(36).substr(2, 8);
  },

  /**
   * 브라우저 및 환경 정보 수집 (봇 탐지용)
   * @returns {object} 브라우저 정보 객체
   * from: section_select.js
   */
  initBrowserInfo: function () {
    return {
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
  },

  /**
   * 마우스 궤적 수집 리스너 설정
   * @param {Array} logArray - 마우스 궤적을 저장할 배열
   * @param {number} interval - 수집 간격 (ms)
   * @param {number} startTime - 시작 시간
   * @param {boolean} normalized - 정규화 좌표 포함 여부
   * from: perf_list.js, queue.js, section_select.js, seat_select.js
   */
  initMouseTracking: function (logArray, interval, startTime, normalized = false) {
    let lastMouseTime = 0;

    const handler = (e) => {
      const now = Date.now();
      if (now - lastMouseTime >= interval) {
        const point = {
          x: e.clientX,
          y: e.clientY
        };

        if (normalized) {
          point.nx = e.clientX / window.innerWidth;
          point.ny = e.clientY / window.innerHeight;
        }

        if (startTime) {
          point.timestamp = now - startTime;
        } else {
          point.t = now - startTime;
        }

        logArray.push(point);
        lastMouseTime = now;
      }
    };

    document.addEventListener('mousemove', handler);
    return handler;  // 나중에 제거할 수 있도록 반환
  },

  // ============== 페이지별 로그 초기화 ==============

  /**
   * 공연 목록 페이지 로그 초기화
   * @returns {object} 로그 데이터 객체
   * from: perf_list.js
   */
  initPerfListLog: function () {
    const sessionId = this.generateSessionId('perf');
    const logData = {
      session_id: sessionId,
      stage: 'perf',
      page_entry_time: new Date().toISOString(),
      performance_id: null,
      actions: [],
      mouse_trajectory: [],
      card_clicks: [],
      date_selections: [],
      time_selections: []
    };

    // 마우스 궤적 수집 시작 (100ms 간격)
    const pageStartTime = new Date(logData.page_entry_time).getTime();
    this.initMouseTracking(logData.mouse_trajectory, 100, pageStartTime, false);

    return logData;
  },

  /**
   * 대기열 페이지 로그 초기화
   * @param {string} perfId - 공연 ID
   * @param {string} selectedDate - 선택한 날짜
   * @param {string} selectedTime - 선택한 시간
   * @param {number} totalQueue - 전체 대기 인원
   * @param {number} initialPosition - 초기 대기 순번
   * @returns {object} 로그 데이터 객체
   * from: queue.js
   */
  initQueueLog: function (perfId, selectedDate, selectedTime, totalQueue, initialPosition) {
    const sessionId = this.generateSessionId('que');
    const logData = {
      session_id: sessionId,
      stage: 'que',
      performance_id: perfId || '',
      selected_date: selectedDate || '',
      selected_time: selectedTime || '',
      queue_start_time: new Date().toISOString(),
      initial_position: initialPosition || 0,
      total_queue: totalQueue || 0,
      position_updates: [],
      queue_end_time: null,
      final_position: null,
      wait_duration_ms: null,
      mouse_trajectory: []
    };

    // 마우스 궤적 수집 시작 (30ms 간격)
    const startTime = new Date(logData.queue_start_time).getTime();
    this.initMouseTracking(logData.mouse_trajectory, 30, startTime, false);

    return logData;
  },

  /**
   * 예매 세션 로그 초기화 (구역 선택 시작)
   * @param {string} perfId - 공연 ID
   * @param {string} selectedDate - 선택한 날짜
   * @param {string} selectedTime - 선택한 시간
   * @returns {object} 로그 데이터 객체
   * from: section_select.js
   */
  initBookLog: function (perfId, selectedDate, selectedTime) {
    const sessionId = this.generateSessionId('book');
    const bookLogData = {
      session_id: sessionId,
      stage: 'book',
      performance_id: perfId || '',
      selected_date: selectedDate || '',
      selected_time: selectedTime || '',
      booking_start_time: new Date().toISOString(),
      viewport: { w: window.innerWidth, h: window.innerHeight },
      browser_info: this.initBrowserInfo(),
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

    // sessionStorage에 저장
    this.saveBookLog(bookLogData);

    return bookLogData;
  },

  /**
   * 좌석 선택 페이지 로그 초기화
   * @param {string} sessionId - 세션 ID
   * @returns {object} 로그 데이터 객체
   * from: seat_select.js
   */
  initSeatSelectionLog: function (sessionId) {
    const pageStartTime = Date.now();
    const logData = {
      session_id: sessionId,
      page: 'seat_selection',
      page_entry_time: new Date(pageStartTime).toISOString(),
      mouse_trajectory: [],
      clicks: [],
      hovers: []
    };

    return { logData, pageStartTime };
  },

  // ============== 로그 전송 함수 ==============

  /**
   * Stage 로그 전송 (perf, que, book)
   * @param {object} logData - 로그 데이터
   * @returns {Promise} fetch 프로미스
   * from: perf_list.js, queue.js, discount_select.js
   */
  sendStageLog: async function (logData) {
    try {
      const response = await fetch('/api/stage-log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(logData)
      });
      return response;
    } catch (error) {
      console.error('Failed to send stage log:', error);
      throw error;
    }
  },

  /**
   * 세션 로그 전송
   * @param {object} sessionData - 세션 데이터
   * @returns {Promise} fetch 프로미스
   * from: seat_select.js
   */
  sendSessionLog: async function (sessionData) {
    try {
      const response = await fetch('/api/session-log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sessionData)
      });
      return response;
    } catch (error) {
      console.error('Failed to send session log:', error);
      throw error;
    }
  },

  /**
   * 예매 완료 로그 전송
   * @param {object} sessionData - 세션 데이터
   * @returns {Promise} fetch 프로미스
   * from: payment.js
   */
  sendCompleteLog: async function (sessionData) {
    try {
      const response = await fetch('/api/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sessionData)
      });
      return response.json();
    } catch (error) {
      console.error('Failed to send complete log:', error);
      throw error;
    }
  },

  // ============== SessionStorage 관리 ==============

  /**
   * SessionStorage에서 bookLogData 가져오기
   * @returns {object|null} bookLogData 또는 null
   * from: seat_select.js, discount_select.js, payment.js
   */
  getBookLog: function () {
    try {
      const data = sessionStorage.getItem('bookLogData');
      return data ? JSON.parse(data) : null;
    } catch (e) {
      console.error('Failed to get book log:', e);
      return null;
    }
  },

  /**
   * SessionStorage에 bookLogData 저장
   * @param {object} data - 저장할 데이터
   * from: section_select.js, seat_select.js
   */
  saveBookLog: function (data) {
    try {
      sessionStorage.setItem('bookLogData', JSON.stringify(data));
    } catch (e) {
      console.error('Failed to save book log:', e);
    }
  },

  /**
   * SessionStorage에서 bookLogData 제거
   * from: discount_select.js, payment.js
   */
  clearBookLog: function () {
    try {
      sessionStorage.removeItem('bookLogData');
    } catch (e) {
      console.error('Failed to clear book log:', e);
    }
  }
};

// 전역 객체로 노출
window.LogCollector = LogCollector;
