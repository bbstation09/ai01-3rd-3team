# FairTicket WBS (Work Breakdown Structure) - Final Ver3

## 👨‍💻 역할 분담 (R&R) - Advanced
*   **Dev 1 (Frontend)**: React Canvas 좌석표(Auto-Click 방어), Dynamic DOM(버튼 조작 방지) 구현.
*   **Dev 2 (Backend)**: **Token Validation(대기열 우회)**, **Time-Lock(미리 입장)**, **Random Queue(취소표 지연)** 구현.
*   **AI 1 (Analysis)**: 순수 로그 분석. **Human Latency(밀리초 차단)**, **Error Reaction(이선좌 반응)**, **Payment Hash** 모델 개발.
*   **AI 2 (Vision)**: OCR+Face 키오스크 및 **Canvas 좌표 기반 가속도(Velocity)** 분석 로직 지원.

## 🗓️ 주차별 일정 (Weekly Focus - Advanced Security)

### Week 2: 기본 방어 (Basic Defense)
*   **Dev 2**: 대기열 토큰 검증 미들웨어 & Time-Lock 로직.
*   **AI 1**: `Response_Time < 150ms` 차단 룰 및 로깅 시스템(Redis) 구축.
*   **AI 2**: 신분증 OCR 모듈 테스트.

### Week 3: 지능형 방어 (Smart Defense)
*   **Dev 1**: 좌석표 Canvas 렌더링 & 마우스 이벤트 좌표 수집기(SDK).
*   **AI 1**: `Error Reaction Analysis` (에러 후 재시도 텀 분석) & `Sequence Entropy` (직선 이동 탐지).
*   **AI 2**: 얼굴 대조 모델 및 Liveness Check.

### Week 4: 고도화 & 리허설 (Deep Dive)
*   **AI 1**: **결제 수단 해시(Payment Hash)** 분석 및 연쇄 차단 로직.
*   **Dev 2**: 취소표 **Random Delay Queue** 적용.
*   **All**: Red Team(매크로 공격) vs Blue Team(방어) 시뮬레이션.

### Week 6: 최종 발표 (Final)
*   **PM**: "9가지 공격 패턴 완벽 방어" 시연 영상 및 기술 문서화.
