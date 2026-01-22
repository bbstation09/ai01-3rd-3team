"""
Seat Selection Module
좌석선택 자동화 로직 (popup_handler.py에서 추출)
"""

import time
import pyautogui
import cv2
import numpy as np
import os
from PIL import ImageGrab

from .vlm_handler import encode_image_to_base64, call_vlm, capture_screen, click_and_restore
from .color_manager import ColorManager


class SeatSelection:
    """좌석선택 자동화 클래스"""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.is_running = False
        self.max_rounds = 5
        self.max_zoom_attempts = 3
        
        self.color_manager = ColorManager()
        self.selected_color = "All Colors"  # 선택된 색상 (콤보박스 값)
        
        # 옵션
        self.auto_zoom = True
        self.prefer_center = True
        self.seat_count = 1  # 선택할 좌석 수 (연속 좌석)
        
        # 모니터 정보
        self.mon_x = 0
        self.mon_y = 0
        self.mon_w = 1920
        self.mon_h = 1080
    
    def update_status(self, message):
        """상태 업데이트"""
        print(f"[SeatSelection] {message}")
        if self.callback:
            self.callback(message)
    
    def set_monitor_region(self, x: int, y: int, w: int, h: int):
        """모니터 영역 설정"""
        self.mon_x = x
        self.mon_y = y
        self.mon_w = w
        self.mon_h = h
    
    def start(self):
        """좌석 선택 시작"""
        self.is_running = True
        self.update_status("=" * 40)
        self.update_status("좌석선택 자동화 시작")
        return self._run_selection()
    
    def stop(self):
        """중지"""
        self.is_running = False
        self.update_status("⏹️ 중지됨")
    
    def _run_selection(self):
        """좌석 선택 메인 로직 (OpenCV 기반)"""
        zoom_attempts = 0
        
        for round_num in range(self.max_rounds):
            if not self.is_running:
                return False
            
            self.update_status(f"\n[라운드 {round_num + 1}] 좌석 분석 중 (OpenCV)...")
            
            # 화면 캡처
            screenshot = capture_screen(self.mon_x, self.mon_y, self.mon_w, self.mon_h)
            width, height = screenshot.size
            # base64_image = encode_image_to_base64(screenshot) # VLM 미사용
            
            # 디버그: 캡처 영역 정보
            self.update_status(f">> 캡처 영역: ({self.mon_x},{self.mon_y}) ~ ({self.mon_x+self.mon_w},{self.mon_y+self.mon_h})")
            
            # OpenCV로 좌석 후보 요청
            seats = self._find_seats_cv(screenshot)
            
            if not seats:
                self.update_status(">> 좌석 후보를 찾을 수 없습니다.")
                
                # 자동 확대
                if self.auto_zoom and zoom_attempts < self.max_zoom_attempts:
                    self.update_status(f">> 확대 시도 ({zoom_attempts + 1}/{self.max_zoom_attempts})...")
                    self._zoom_in()
                    zoom_attempts += 1
                    time.sleep(0.5)
                    continue
                
                time.sleep(1)
                continue
            
            # -------------------------------------------------------------------------
            # 다중 좌석 모드 (Batch Click)
            # -------------------------------------------------------------------------
            if self.seat_count > 1:
                # 연석 로직은 _find_seats_cv에서 처리되어 그룹으로 반환되거나, 개별 상위 좌석이 반환됨
                # 여기서 개수 체크 (연석 로직이 실패해서 낱개만 있으면 개수 부족할 수 있음)
                if len(seats) < self.seat_count:
                    self.update_status(f">> 좌석 부족: {len(seats)}개 발견 (필요: {self.seat_count}개)")
                    time.sleep(1)
                    continue
                
                self.update_status(f">> {self.seat_count}개 연석 클릭 시도...")
                
                # 필요한 개수만큼 순차 클릭
                for i in range(self.seat_count):
                    self._click_seat(seats[i], i+1, width, height)
                    time.sleep(0.3) # 연석 클릭 간격 (웹사이트 반응 대기)
                
                # 확인 및 대화창 처리
                time.sleep(0.5)
                pyautogui.press('enter')
                
                if self._check_seat_selected():
                    self.update_status(">> 좌석 선택 성공!")
                    self._click_payment_button()
                    return True
                else:
                    self.update_status(">> 선택 실패. 다음 라운드...")
            
            # -------------------------------------------------------------------------
            # 단일 좌석 모드 (Iterative Click)
            # -------------------------------------------------------------------------
            else:
                self.update_status(f">> {len(seats)}개 좌석 후보 발견")
                
                for i, seat in enumerate(seats):
                    if not self.is_running:
                        return False
                    
                    self._click_seat(seat, i+1, width, height)
                    time.sleep(0.5)
                    
                    # 대화창 처리
                    pyautogui.press('enter')
                    time.sleep(0.3)
                    
                    # 선택 성공 여부 확인
                    if self._check_seat_selected():
                        self.update_status(">> 좌석 선택 성공!")
                        self._click_payment_button()
                        return True
            
            self.update_status(f">> 라운드 {round_num + 1} 좌석 모두 실패. 다음 라운드...")
            time.sleep(0.5)
        
        self.update_status(">> 모든 라운드 실패. 좌석 선택 종료.")
        return False


    def _find_seats_cv(self, screenshot):
        """OpenCV를 이용한 좌석 탐색"""
        # PIL -> OpenCV (BGR)
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        h, w = img.shape[:2]
        
        # HSV 변환
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # =================================================================
        # [1단계] 좌석 영역 감지 (회색+색상 모든 좌석 포함)
        # =================================================================
        # 회색 좌석 마스크 (판매완료 좌석)
        gray_lower = np.array([0, 0, 100])
        gray_upper = np.array([180, 30, 200])
        gray_mask = cv2.inRange(hsv, gray_lower, gray_upper)
        
        # 색상 좌석 마스크 (선택 가능한 좌석)
        self.color_manager.load_colors(self.selected_color)
        color_mask = self.color_manager.get_mask(hsv)
        
        # 모든 좌석 마스크 합치기
        all_seats_mask = cv2.bitwise_or(gray_mask, color_mask)
        
        # 노이즈 제거 및 연결
        kernel = np.ones((5,5), np.uint8)
        all_seats_mask = cv2.morphologyEx(all_seats_mask, cv2.MORPH_CLOSE, kernel)
        all_seats_mask = cv2.morphologyEx(all_seats_mask, cv2.MORPH_OPEN, kernel)
        
        # 좌석 영역 바운딩 박스 계산
        seat_contours, _ = cv2.findContours(all_seats_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not seat_contours:
            return []
        
        # 가장 큰 영역 = 좌석 맵
        largest_contour = max(seat_contours, key=cv2.contourArea)
        seat_x, seat_y, seat_w, seat_h = cv2.boundingRect(largest_contour)
        
        self.update_status(f">> 좌석 영역 감지: ({seat_x},{seat_y}) ~ ({seat_x+seat_w},{seat_y+seat_h})")
        
        # =================================================================
        # [2단계] 좌석 영역 내에서만 색상 좌석 탐색
        # =================================================================
        # 노이즈 제거 (색상 마스크)
        kernel = np.ones((3,3), np.uint8)
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel)
        
        # 외곽선 검출
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 1차 후보 수집 (좌석 영역 내만)
        raw_candidates = []
        min_area = 30
        max_area = 500
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area or area > max_area:
                continue
                
            # 중심점 계산
            M = cv2.moments(cnt)
            if M["m00"] == 0: continue
            
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
            # 좌석 영역 내에 있는지 확인
            if not (seat_x <= cx <= seat_x + seat_w and seat_y <= cy <= seat_y + seat_h):
                continue  # 좌석 영역 밖이면 제외 (범례 등)
            
            raw_candidates.append((cx, cy, area))
        
        # 2차 필터: 밀집도 검사 (실제 좌석은 촘촘, 범례는 떨어져 있음)
        density_radius = 30   # 반경 30px (좌석 간격 고려)
        min_neighbors = 3     # 최소 3개 이웃 필요 (범례 필터링)
        
        # 밀집도 필터 통과한 좌석만 수집
        filtered_seats = []
        for i, (cx, cy, area) in enumerate(raw_candidates):
            neighbor_count = 0
            for j, (ox, oy, _) in enumerate(raw_candidates):
                if i == j: continue
                dist = ((cx - ox)**2 + (cy - oy)**2) ** 0.5
                if dist < density_radius:
                    neighbor_count += 1
            
            if neighbor_count >= min_neighbors:
                filtered_seats.append((cx, cy, area))
        
        # [FALLBACK] 밀집도 필터로 모두 제거되면, 원본 사용 (잔여 좌석이 적을 때)
        if not filtered_seats and raw_candidates:
            self.update_status(">> 밀집도 필터 완화 (잔여 좌석 적음)")
            filtered_seats = raw_candidates  # 원본 사용
        
        # 좌석이 없으면 빈 리스트 반환
        if not filtered_seats:
            return []
        
        # =================================================================
        # [동적 스테이지/중앙 계산] 좌석 영역 기반
        # =================================================================
        all_x = [s[0] for s in filtered_seats]
        all_y = [s[1] for s in filtered_seats]
        
        # 좌석 영역의 중앙 X좌표
        dynamic_center_x = (min(all_x) + max(all_x)) // 2
        # 스테이지 기준 Y좌표 (가장 위쪽 좌석 = 스테이지에 가장 가까움)
        stage_y = min(all_y)
        
        self.update_status(f">> 동적 계산: center_x={dynamic_center_x}, stage_y={stage_y}")
        # =================================================================
        
        # 점수 계산 (동적 기준 사용)
        seat_candidates = []
        for cx, cy, area in filtered_seats:
            # 스테이지(stage_y)에 가까울수록, 중앙(dynamic_center_x)에 가까울수록 높은 점수
            dist_from_stage = cy - stage_y  # 상단(스테이지)에서 멀어질수록 증가
            dist_from_center = abs(cx - dynamic_center_x)
            
            # 점수 (낮을수록 좋음) - 앞줄(낮은 y) + 중앙 선호
            score = (dist_from_stage * 2.0) + (dist_from_center * 1.0)
            quality = max(0, 100 - int(score / 500 * 100))  # 500px 기준 정규화
            
            seat_candidates.append({
                "x_px": cx,
                "y_px": cy,
                "score": score,
                "quality": quality,
                "reason": "OpenCV detected"
            })
            
        # 점수 기준 정렬 (score 오름차순: 작은게 좋은거)
        seat_candidates.sort(key=lambda s: s["score"])
        
        # 연석 처리 로직
        # 연석 처리 로직
        if self.seat_count > 1 and len(seat_candidates) >= self.seat_count:
            final_seats = self._find_consecutive_seats(seat_candidates)
        else:
            final_seats = seat_candidates[:5] # 상위 5개 반환
            
        # =================================================================
        # [DEBUG] 시각화 저장 (사용자 요청)
        # =================================================================
        try:
            debug_img = img.copy()
            
            # 1. 모든 후보 (초록색)
            for s in seat_candidates:
                cv2.circle(debug_img, (s['x_px'], s['y_px']), 3, (0, 255, 0), -1)
                
            # 2. 최종 선택 (빨간색 + 강조)
            for i, s in enumerate(final_seats):
                cv2.circle(debug_img, (s['x_px'], s['y_px']), 5, (0, 0, 255), -1)
                cv2.putText(debug_img, f"{i+1}", (s['x_px']+5, s['y_px']-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # 저장
            if not os.path.exists("temp"):
                os.makedirs("temp")
            save_path = f"temp/debug_cv_result_{int(time.time())}.png"
            cv2.imwrite(save_path, debug_img)
            self.update_status(f">> 디버그 이미지 저장됨: {save_path}")
        except Exception as e:
            # candidates 변수명 오류 가능성 있으므로 수정
            try:
                # Retry with correct variable name if first attempt failed
               pass
            except:
                print(f"Debug save failed: {e}")
        # =================================================================
        
        return final_seats

    def _find_consecutive_seats(self, candidates):
        """연석 찾기 로직"""
        # y축(행)으로 먼저 그룹핑
        rows = {}
        y_threshold = 10 # 같은 행으로 볼 y 차이 허용치
        
        for seat in candidates:
            added = False
            for y_key in rows:
                if abs(seat["y_px"] - y_key) < y_threshold:
                    rows[y_key].append(seat)
                    added = True
                    break
            if not added:
                rows[seat["y_px"]] = [seat]
        
        best_group = []
        best_score_avg = float('inf')
        
        # 각 행에서 x축으로 정렬 후 연속성 확인
        x_threshold = 15 # 좌석 간 x 거리 허용치 (인접 좌석만 허용)
        
        for y_key, row_seats in rows.items():
            if len(row_seats) < self.seat_count:
                continue
                
            row_seats.sort(key=lambda s: s["x_px"])
            
            # 슬라이딩 윈도우로 연속 확인
            for i in range(len(row_seats) - self.seat_count + 1):
                group = row_seats[i : i+self.seat_count]
                
                # 연속성 검사
                is_consecutive = True
                for j in range(len(group)-1):
                    dist = group[j+1]["x_px"] - group[j]["x_px"]
                    if dist > x_threshold: # 너무 멀면 연속 아님
                        is_consecutive = False
                        break
                
                if is_consecutive:
                    # 평균 점수 계산
                    avg_score = sum(s["score"] for s in group) / len(group)
                    if avg_score < best_score_avg:
                        best_score_avg = avg_score
                        best_group = group
        
        if best_group:
            self.update_status(f">> {self.seat_count}연석 찾음! (점수: {best_score_avg:.1f})")
            return best_group
        
        self.update_status(">> 연석을 찾을 수 없어 개별 좌석 반환")
        return candidates[:5]

    def _get_seat_candidates(self, base64_image, width, height):
        """VLM으로 좌석 후보 반환 (품질 점수 포함)"""
        
        # 수량에 따른 연속 좌석 요청
        if self.seat_count > 1:
            seat_request = f"""Find {self.seat_count} CONSECUTIVE seats in the SAME ROW (horizontally adjacent colored squares).
Return each seat's coordinates. Seats should be next to each other horizontally."""
        else:
            seat_request = "Find up to 5 individual available seats."
        
        prompt = f"""Image size: {width}x{height} pixels.

This is a ticket booking page.
Find {self.seat_count} AVAILABLE seat(s) in the seating grid.

VISUAL CLUES:
- AVAILABLE seats are COLORED squares/boxes (Blue, Green, Purple, Pink, Orange, etc.)
- UNAVAILABLE seats are White, Gray, or Empty outlines.

TASK:
1. Locate the grid of small squares.
2. Find colored squares (filled with color).
3. Select specific seats based on count: {seat_request}

OUTPUT FORMAT (JSON only):
{{"seats": [
    {{"x_px": 1234, "y_px": 567, "quality": 100, "reason": "colored seat"}}
]}}

CRITICAL:
- Return PIXEL COORDINATES (integers), NOT 0.0-1.0 normalized values.
- Example: x_px: 450, y_px: 300
- Do NOT return empty if you see any colored squares.
- Quality score: Higher for seats closer to the "STAGE" (top) and center.
"""

        result = call_vlm(prompt, base64_image, max_tokens=600)
        seats = result.get("seats", [])
        
        # 디버그: VLM 응답 출력
        if seats:
            self.update_status(f">> VLM 반환: {len(seats)}개 좌석")
            for i, s in enumerate(seats[:3]):  # 상위 3개만 표시
                # 픽셀 좌표 확인
                if "x_px" in s:
                    pos_str = f"x_px={s['x_px']}, y_px={s['y_px']}"
                else:
                    pos_str = f"x={s.get('x',0)}, y={s.get('y',0)}"
                    
                quality = s.get("quality", 0)
                reason = s.get("reason", "")[:20]
                self.update_status(f"   [{i+1}] {pos_str}, Q={quality} ({reason}...)")
        
        # 1석일 때만 품질 순으로 정렬 (다중 좌석은 연석 유지를 위해 순서 보존)
        if self.seat_count == 1:
            seats.sort(key=lambda s: s.get("quality", 0), reverse=True)
        
        return seats


    def _click_seat(self, seat, idx, width, height):
        """개별 좌석 클릭 헬퍼"""
        
        # 1. 픽셀 좌표가 있는 경우 (우선 사용)
        if "x_px" in seat and "y_px" in seat:
            try:
                x_px = int(seat["x_px"])
                y_px = int(seat["y_px"])
                abs_x = self.mon_x + x_px
                abs_y = self.mon_y + y_px
                quality = seat.get("quality", 0)
                
                self.update_status(f">> 클릭 [{idx}]: ({abs_x}, {abs_y}) [PX MODE] Q={quality}")
                click_and_restore(abs_x, abs_y)
                return
            except (ValueError, TypeError):
                self.update_status(f">> [{idx}] 픽셀 좌표 오류, 정규화 좌표 시도...")
        
        # 2. 정규화 좌표 사용 (Fallback)
        raw_x = seat.get("x", 0)
        raw_y = seat.get("y", 0)
        quality = seat.get("quality", 0)
        
        try:
            norm_x = float(raw_x)
            norm_y = float(raw_y)
        except (ValueError, TypeError):
            self.update_status(f">> [{idx}] 좌표 오류")
            return

        if norm_x > 1.0: norm_x /= width
        if norm_y > 1.0: norm_y /= height
        
        abs_x = self.mon_x + int(norm_x * width)
        abs_y = self.mon_y + int(norm_y * height)
        
        self.update_status(f">> 클릭 [{idx}]: ({abs_x}, {abs_y}) [NORM MODE] Q={quality}")
        click_and_restore(abs_x, abs_y)
    
    def _check_seat_selected(self):
        """좌석 선택 성공 여부 확인"""
        screenshot = capture_screen(self.mon_x, self.mon_y, self.mon_w, self.mon_h)
        base64_image = encode_image_to_base64(screenshot)
        
        # 좌석 수량을 명시하여 확인
        prompt = f"""Check if {self.seat_count} seat(s) have been selected.

Look for text like:
- "총 {self.seat_count}석 선택되었습니다"
- "{self.seat_count}석 선택"
- "선택좌석" section showing {self.seat_count} seat(s)

If the selected count matches {self.seat_count}, return true.

JSON only:
{{"selected": true}} or {{"selected": false}}"""
        
        result = call_vlm(prompt, base64_image, max_tokens=50)
        return result.get("selected", False)
    
    def _click_payment_button(self):
        """결제 버튼 클릭"""
        screenshot = capture_screen(self.mon_x, self.mon_y, self.mon_w, self.mon_h)
        width, height = screenshot.size
        base64_image = encode_image_to_base64(screenshot)
        
        prompt = f"""Screenshot size: {width}x{height} pixels.

Find the "좌석선택완료" button in the WEB BROWSER area (LEFT side of the screen).
The button is typically BLUE and located at the bottom of the seat selection panel.

IMPORTANT: Ignore the RIGHT side - that's the app control panel, not the website.
The website is on the LEFT side (x < 0.5).

Return its CENTER coordinates.
CRITICAL: Coordinates MUST be 0.0-1.0 normalized!

JSON only:
{{"x": 0.xx, "y": 0.xx}}"""
        
        result = call_vlm(prompt, base64_image, max_tokens=100)
        
        try:
            norm_x = float(result.get("x", 0))
            norm_y = float(result.get("y", 0))
        except (ValueError, TypeError):
            self.update_status(">> 결제 버튼 좌표 변환 실패")
            return
        
        if norm_x > 0 and norm_y > 0:
            if norm_x > 1.0:
                norm_x = norm_x / width
            if norm_y > 1.0:
                norm_y = norm_y / height
            
            abs_x = self.mon_x + int(norm_x * width)
            abs_y = self.mon_y + int(norm_y * height)
            
            self.update_status(f">> 결제 버튼 클릭: ({abs_x}, {abs_y}) [norm: {norm_x:.4f}, {norm_y:.4f}]")
            click_and_restore(abs_x, abs_y)
    
    def _zoom_in(self):
        """좌석 맵 확대"""
        target_x = self.mon_x + int(self.mon_w * 0.3)
        target_y = self.mon_y + int(self.mon_h * 0.5)
        
        pyautogui.moveTo(target_x, target_y)
        time.sleep(0.2)
        pyautogui.scroll(3)
        time.sleep(0.3)


# 모듈 레벨 함수
def create_seat_selection(callback=None):
    """SeatSelection 인스턴스 생성"""
    return SeatSelection(callback)
