# FairTicket: 불법 암표 근절을 위한 AI 기반 티케팅 & 입장 솔루션 (Final Ver4.1)

## 1. 추진 배경: 2025년, 암표와의 전쟁 (Background)
*   **폭증하는 암표**: 2025년 8월 기준 암표 신고 **약 26만 건** (5년 전 대비 **40배** 폭증).
*   **시장의 붕괴**: 한국시리즈 티켓이 정가의 100배인 **999만 원**에 거래. 휠체어석까지 매크로의 먹잇감이 됨.
*   **기술적 참패**: '매크로 금지법' 등 법적 제재가 강화되었으나, **VPN 우회/패킷 전송(Railgun)** 등 고도화된 기술 앞에서는 입증과 단속이 불가능한 한계 봉착.
*   **자동화의 확산 (Macro Scheduler)**: 단순 티켓팅 툴을 넘어, **댓글 부대(여론 조작)** 등에서 악용되던 **자동 스케줄러(Auto-Login, Click, Post)** 기술이 암표 시장에 유입되어 일반인도 쉽게 사용하는 범용 위협으로 진화.
*   **결론**: 사후 처벌이 아닌, **"기술적 원천 봉쇄(AI Defense)"**만이 유일한 해결책.

## 2. 프로젝트 개요 (Executive Summary)
*   **목표**: **"광클(Spam Click)이 통하지 않는 시스템"**과 스마트 입장으로 Full-Cycle Protection 달성.
*   **팀 구성/기간**: 4인 / 1.5개월

## 3. 암표상 패턴 분석 및 대응 전략 (9 Core Patterns)

| Category | 공격 패턴 (Attack) | FairTicket 대응 전략 (Defense - Ultimate) |
| :--- | :--- | :--- |
| **Speed** | **1. 밀리초 예매** (광클) | **Random Button Jump**: 예매 오픈 순간 버튼 위치 변경. 허공 클릭 유도 후 **반응 속도(Rule < 0.15s)** 로 차단. |
| **Speed** | **2. 대기열 미리 입장** | **Time-Lock**: 오픈 시간 전 세션 **강제 만료(Kick)**. |
| **Logick** | **3. 이선좌 무시** `(Retry)` | **Error Panic**: 에러 직후 **0.1초 내 재클릭** 시 봇 판정. |
| **Logic** | **4. 취소표 은닉** | **Random Queue**: 취소표는 **5~30분 랜덤 딜레이** 후 오픈. |
| **Logic** | **5. 대기열 우회** `(Bypass)` | **Token Validation**: 대기열 서버 토큰 없이 API 접근 불가. |
| **Script** | **6. 자동호출코드** `(Auto)` | **Sequence Entropy**: 예매->결제 경로 복잡도 체크. 직선 주행 차단. |
| **Script** | **7. 버튼 선 활성화** | **Dynamic DOM**: DOM ID/Class를 매번 난수화. |
| **Script** | **8. 좌석 자동선택** | **Deep Latency**: 로딩(`T0`)~클릭(`T1`) 시간이 **0.5초** 미만이면 차단. |
| **Fraud** | **9. 결제 뚫기** | **Payment Hash**: 동일 카드/계좌 해시 공유 시 연쇄 차단. |

## 4. 핵심 전략 요약
1.  **Defense**: "인간의 반응 속도"를 물리적 척도로 삼는 방어.
2.  **Forensics**: 환불 시 로그 역추적.
3.  **Entry**: 현장 스마트 키오스크의 물리적 방어.

## 5. 기술 스택 (Tech Stack)
*   **Backend**: FastAPI, Redis, ELK.
*   **AI**: LSTM (시퀀스), Random Forest, FaceNet.
