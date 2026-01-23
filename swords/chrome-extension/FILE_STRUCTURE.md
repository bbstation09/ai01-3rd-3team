# 📁 Chrome Extension 파일 구조

```
chrome-extension/
│
├── 📄 manifest.json              # Extension 설정 (Manifest V3)
├── 📄 background.js              # Background service worker
├── 📄 content.js                 # 메인 content script (진입점)
│
├── 📂 core/                      # 핵심 엔진
│   ├── fsm.js                   # Finite State Machine 엔진
│   └── recovery.js              # 에러 복구 관리자
│
├── 📂 states/                    # 상태 핸들러들
│   ├── base.js                  # 기본 State 클래스
│   ├── idle.js                  # IDLE 상태
│   ├── wait_open.js             # 대기 상태
│   ├── click_start.js           # 예매 버튼 클릭
│   ├── handle_popup.js          # 팝업 처리
│   ├── select_zone.js           # 구역 선택
│   ├── select_seat.js           # 좌석 선택 ⭐
│   ├── confirm.js               # 확인 버튼
│   ├── payment.js               # 결제 페이지 (성공)
│   └── error.js                 # 에러/실패 처리
│
├── 📂 utils/                     # 유틸리티
│   ├── logger.js                # 구조화된 로거
│   └── dom.js                   # DOM 조작 함수들
│
├── 📂 config/                    # 설정
│   └── sites.js                 # 사이트별 selector 설정
│
├── 📂 popup/                     # Extension UI
│   ├── popup.html               # Popup HTML
│   ├── popup.js                 # Popup 로직
│   └── popup.css                # Popup 스타일
│
├── 📂 icons/                     # Extension 아이콘
│   ├── icon16.png               # (필요)
│   ├── icon48.png               # (필요)
│   └── icon128.png              # (필요)
│
├── 📂 test/                      # 테스트 파일
│   └── mock-ticket-page.html   # Mock 테스트 페이지
│
└── 📂 docs/                      # 문서
    ├── README.md                # 전체 문서
    ├── ARCHITECTURE.md          # 아키텍처 설명
    ├── TESTING.md               # 테스트 가이드
    └── QUICKSTART.md            # 빠른 시작 ⭐
```

## 📝 파일별 역할

### 핵심 파일 (반드시 이해)

| 파일 | 역할 | 중요도 |
|------|------|--------|
| `manifest.json` | Extension 설정, 권한, 스크립트 로드 순서 | ⭐⭐⭐ |
| `core/fsm.js` | 상태 전환 로직, 전체 흐름 제어 | ⭐⭐⭐ |
| `states/base.js` | 모든 State의 기본 클래스 | ⭐⭐⭐ |
| `config/sites.js` | 사이트별 CSS selector 설정 | ⭐⭐⭐ |
| `content.js` | 진입점, FSM 초기화 | ⭐⭐ |

### State 파일들 (필요시 수정)

- `states/select_seat.js` - 좌석 선택 로직 (가장 복잡)
- `states/handle_popup.js` - 팝업 처리 로직
- 나머지는 간단한 버튼 클릭 로직

### UI 파일

- `popup/` - Extension 아이콘 클릭 시 나타나는 설정 창

### 테스트용

- `test/mock-ticket-page.html` - 안전하게 테스트할 수 있는 가짜 페이지

## 🔧 주요 수정 포인트

실제 사이트에 맞춰 수정해야 할 파일:

1. **`config/sites.js`** - 사이트의 실제 CSS selector로 변경
2. **`states/select_seat.js`** - 사이트의 좌석 구조에 맞춰 로직 조정
3. **`manifest.json`** - host_permissions에 타겟 사이트 추가

## 📚 추천 읽기 순서

1. [QUICKSTART.md](QUICKSTART.md) - 3분 안에 테스트
2. [TESTING.md](TESTING.md) - 단계별 테스트 방법
3. [ARCHITECTURE.md](ARCHITECTURE.md) - 전체 구조 이해
4. [README.md](README.md) - 상세 문서

---

**시작**: [QUICKSTART.md](QUICKSTART.md) 부터 보세요! 🚀
