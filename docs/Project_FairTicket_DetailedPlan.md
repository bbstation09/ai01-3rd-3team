# FairTicket 상세 기획서 (Detailed Plan) - Final Ver4

## 1. 암표상 공격 패턴별 대응 상세 (Ultimate Countermeasures)

### ⚡ Group A: 속도/반응 (Speed & Reaction)
*   **Pattern 1: 밀리초 예매 (Spam Clicker Defesne)**
    *   **공격**: 버튼 활성화 전부터 1초에 100번씩 클릭을 난사(Spamming)하여 0.001초 만에 진입 시도.
    *   **방어**: **Random Button Jump**.
        *   `Enable` 시점에 버튼 위치를 무작위로 **50px~100px** 이동시킴.
        *   난사하던 봇은 이동 전 좌표(허공)를 클릭하게 됨.
        *   이동된 버튼을 눈으로 보고 마우스를 옮겨 클릭하는 **[Reaction Time]** 측정.
        *   **Rule**: `Reaction < 150ms` 이면 차단.
*   **Pattern 3: 이선좌 무시 (Panic Check)**
    *   **공격**: 에러 팝업을 무시하고 0.01초 만에 다른 좌석 클릭.
    *   **방어**: **Error Panic Analysis**.
        *   에러 발생 직후 0.2초 이내 재요청은 **기계적 재시도(Retry logic)**로 간주.

### 🛡️ Group B: 조작/우회 (Manipulation)
*   **Pattern 8: 좌석 자동선택 (Deep Latency)**
    *   **공격**: 이미지 처리로 명당 좌표 추출 후 직행.
    *   **방어**: **Visual Search Latency**.
        *   좌석표 로딩 완료(`Load_End`) 시점부터 첫 좌석 클릭(`Click`)까지 시간 측정.
        *   수천 개의 포도알 중 내가 원하는 자리를 찾는 **[인지 시간(0.2s) + 이동 시간(0.3s)]** 고려.
        *   **Rule**: `Total Latency < 0.5s` 이면 차단.

### 💰 Group C: 정책/금융 (Policy)
*   **Pattern 4: 취소표 은닉**: **Random Release Queue** (5~30분 랜덤 지연 오픈).
*   **Pattern 9: 결제 수단 뚫기**: **Payment Hash Sharing** (동일 카드/계좌 사용 계정 연쇄 차단).

---

## 2. 데이터 흐름 (Advanced Data Flow)
1.  **Request**: User Interaction.
2.  **SDK Probe**:
    *   `Button_Pos_Init` vs `Click_Pos` (허공 클릭 여부).
    *   `Visual_Search_Time` (좌석표 로딩 후 딜레이).
3.  **Real-time Analysis**:
    *   `Reaction Time` < 150ms? -> **Spam Bot**.
    *   `Search Time` < 500ms? -> **CV Bot**.
4.  **Decision**: **Pass / Block**.

## 3. 핵심 기술 (Core Tech)
*   **Frontend**: React (State 변조를 통한 버튼 좌표 Randomization).
*   **Backend**: Redis (Time-series Log).
