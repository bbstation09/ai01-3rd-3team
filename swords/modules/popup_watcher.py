"""
Popup Watcher Module
백그라운드 팝업/대화창/CAPTCHA 감시 및 처리
"""

import time
import threading
import pyautogui
from PIL import ImageGrab

from .vlm_handler import encode_image_to_base64, call_vlm, capture_screen, click_and_restore


class PopupWatcher:
    """백그라운드 팝업 감시 클래스"""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.is_running = False
        self.watch_thread = None
        self.check_interval = 1.0  # 1초 간격
        
        # 모니터 정보
        self.mon_x = 0
        self.mon_y = 0
        self.mon_w = 1920
        self.mon_h = 1080
        
        # 통계
        self.handled_count = 0
    
    def update_status(self, message):
        """상태 업데이트"""
        print(f"[PopupWatcher] {message}")
        if self.callback:
            self.callback(message)
    
    def set_monitor_region(self, x: int, y: int, w: int, h: int):
        """모니터 영역 설정"""
        self.mon_x = x
        self.mon_y = y
        self.mon_w = w
        self.mon_h = h
    
    def start(self):
        """팝업 감시 시작"""
        if self.is_running:
            return
        
        self.is_running = True
        self.handled_count = 0
        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()
        self.update_status("👁️ 팝업 감시 시작")
    
    def stop(self):
        """팝업 감시 중지"""
        self.is_running = False
        self.update_status(f"⏹️ 팝업 감시 중지 (처리: {self.handled_count}건)")
    
    def _watch_loop(self):
        """팝업 감시 루프"""
        while self.is_running:
            try:
                result = self._detect_and_handle_popup()
                if result:
                    self.handled_count += 1
            except Exception as e:
                print(f"PopupWatcher error: {e}")
            
            time.sleep(self.check_interval)
    
    def _detect_and_handle_popup(self):
        """팝업 감지 및 처리"""
        # 화면 캡처
        screenshot = capture_screen(self.mon_x, self.mon_y, self.mon_w, self.mon_h)
        width, height = screenshot.size
        base64_image = encode_image_to_base64(screenshot)
        
        # VLM으로 팝업 분석
        prompt = f"""Screenshot size: {width}x{height} pixels.

Find popup type and return JSON only.

Types:
- CONFIRM: Has "확인"/"OK" button -> x,y = button center
- GUIDE: Has "닫기"/"X" button -> x,y = button center
- CAPTCHA: Has distorted text image + input field
  1. READ the distorted characters -> put in "text"
  2. FIND the center of INPUT FIELD (empty box with "보 안 문 자" text inside)
  3. x,y = CENTER of this INPUT FIELD
- LOADING: Loading screen
- NONE: No popup

CRITICAL: Coordinates MUST be 0.0-1.0 normalized!
- x=0.0 is left edge, x=1.0 is right edge
- y=0.0 is top edge, y=1.0 is bottom edge

JSON only:
{{"type":"...","text":"...","x":0.xx,"y":0.xx}}"""

        result = call_vlm(prompt, base64_image, max_tokens=150)
        
        if not result:
            return False
        
        p_type = result.get("type", "NONE").upper()
        p_text = result.get("text", "")
        raw_x = float(result.get("x", 0))
        raw_y = float(result.get("y", 0))
        
        # 정규화 검증
        if raw_x > 1.0:
            norm_x = raw_x / width
        else:
            norm_x = raw_x
            
        if raw_y > 1.0:
            norm_y = raw_y / height
        else:
            norm_y = raw_y
        
        # 좌표 계산
        abs_x = self.mon_x + int(norm_x * width)
        abs_y = self.mon_y + int(norm_y * height)
        
        # 타입별 처리
        if p_type == "NONE":
            return False
        
        elif p_type == "LOADING":
            self.update_status("⏳ 로딩 중...")
            return False
        
        elif p_type in ["CONFIRM", "GUIDE"]:
            if norm_x > 0 and norm_y > 0:
                self.update_status(f"🖱️ {p_type} 처리: 클릭 ({abs_x}, {abs_y})")
                click_and_restore(abs_x, abs_y)
                time.sleep(0.3)
                return True
        
        elif p_type == "CAPTCHA":
            if p_text and norm_x > 0 and norm_y > 0:
                captcha_str = "".join(e for e in p_text if e.isalnum())
                self.update_status(f"🔐 CAPTCHA 처리: '{captcha_str}' 입력")
                
                click_and_restore(abs_x, abs_y)
                time.sleep(0.1)
                pyautogui.write(captcha_str)
                time.sleep(0.1)
                pyautogui.press('enter')
                return True
        
        return False


# 모듈 레벨 함수
def create_popup_watcher(callback=None):
    """PopupWatcher 인스턴스 생성"""
    return PopupWatcher(callback)
