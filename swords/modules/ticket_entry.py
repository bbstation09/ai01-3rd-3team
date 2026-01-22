"""
Ticket Entry Module
예매입장 자동화 로직 (time_click.ahk 변환)
"""

import os
import time
import threading
import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab
from datetime import datetime

from .vlm_handler import click_and_restore


class TicketEntry:
    """예매입장 자동화 클래스"""
    
    def __init__(self, callback=None, on_complete=None):
        self.is_running = False
        self.target_image_path = None
        self.target_time = None
        self.callback = callback  # 상태 업데이트 콜백
        self.on_complete = on_complete  # 완료 시 콜백 (성공 여부 전달)
        self.watch_thread = None
        self.watch_counter = 0
        self.max_watch_count = 6000  # 60초 제한 (10ms * 6000)
        
        # 모니터 정보
        self.mon_left = 0
        self.mon_top = 0
        self.mon_right = 1920
        self.mon_bottom = 1080
        
    def update_status(self, message):
        """상태 업데이트"""
        print(f"[TicketEntry] {message}")
        if self.callback:
            self.callback(message)
    
    def set_target_image(self, image_path: str):
        """대상 이미지 설정"""
        if os.path.exists(image_path):
            self.target_image_path = image_path
            self.update_status(f"✅ 이미지 설정: {os.path.basename(image_path)}")
            return True
        else:
            self.update_status(f"❌ 이미지 파일 없음: {image_path}")
            return False
    
    def set_target_time(self, hour: int, minute: int, second: int):
        """목표 시간 설정"""
        self.target_time = (hour, minute, second)
        self.update_status(f"⏰ 목표 시간: {hour:02d}:{minute:02d}:{second:02d}")
    
    def set_monitor_region(self, left: int, top: int, right: int, bottom: int):
        """감시 영역 설정"""
        self.mon_left = left
        self.mon_top = top
        self.mon_right = right
        self.mon_bottom = bottom
    
    def start_waiting(self):
        """시간 대기 시작"""
        if not self.target_image_path:
            self.update_status("❌ 이미지를 먼저 설정하세요!")
            return False
        
        if not self.target_time:
            self.update_status("❌ 목표 시간을 먼저 설정하세요!")
            return False
        
        self.is_running = True
        self.watch_counter = 0
        self.watch_thread = threading.Thread(target=self._wait_loop, daemon=True)
        self.watch_thread.start()
        return True
    
    def start_watching(self):
        """즉시 감시 시작 (시간 대기 없이)"""
        if not self.target_image_path:
            self.update_status("❌ 이미지를 먼저 설정하세요!")
            return False
        
        self.is_running = True
        self.watch_counter = 0
        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()
        return True
    
    def stop(self):
        """감시 중지"""
        self.is_running = False
        self.update_status("⏹️ 중지됨")
    
    def _wait_loop(self):
        """시간 대기 루프"""
        h, m, s = self.target_time
        target_seconds = h * 3600 + m * 60 + s
        
        while self.is_running:
            now = datetime.now()
            now_seconds = now.hour * 3600 + now.minute * 60 + now.second
            remaining = target_seconds - now_seconds
            
            if remaining <= 0:
                self.update_status("⏰ 오픈 시간! 새로고침 및 감시 시작...")
                pyautogui.press('f5')  # 새로고침
                time.sleep(0.5)
                self._watch_loop()
                return
            
            # 남은 시간 표시
            hh = remaining // 3600
            mm = (remaining % 3600) // 60
            ss = remaining % 60
            self.update_status(f"⏳ 남은 시간: {hh:02d}:{mm:02d}:{ss:02d}")
            
            time.sleep(0.1)
    
    def _watch_loop(self):
        """버튼 감시 루프"""
        self.update_status("🔍 버튼 감시 시작...")
        
        while self.is_running and self.watch_counter < self.max_watch_count:
            self.watch_counter += 1
            
            # 상태 업데이트 (100회마다)
            if self.watch_counter % 100 == 0:
                self.update_status(f"🔍 스캔 중... ({self.watch_counter})")
            
            # 이미지 검색
            found = self._find_button()
            if found:
                x, y = found
                self.update_status(f"✨ 버튼 발견! ({x}, {y}) 클릭...")
                
                # 클릭 (위치 복원)
                click_and_restore(x + 10, y + 10)
                
                self.update_status("🎉 클릭 완료!")
                self.is_running = False
                
                # 완료 콜백 호출
                if self.on_complete:
                    self.on_complete(True)
                return True
            
            time.sleep(0.01)  # 10ms 간격
        
        if self.watch_counter >= self.max_watch_count:
            self.update_status("❌ 시간 초과! 버튼을 찾지 못했습니다.")
        
        self.is_running = False
        
        # 완료 콜백 호출 (실패)
        if self.on_complete:
            self.on_complete(False)
        return False
    
    def _find_button(self):
        """OpenCV를 사용한 이미지 검색 (다중 스케일 지원)"""
        try:
            # 화면 캡처
            screenshot = ImageGrab.grab(bbox=(
                self.mon_left, self.mon_top, 
                self.mon_right, self.mon_bottom
            ))
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
            
            # 타겟 이미지 로드 (캐싱을 위해 첫 로드시만)
            if not hasattr(self, '_template_cache') or self._template_cache is None:
                self._template_cache = cv2.imread(self.target_image_path, cv2.IMREAD_GRAYSCALE)
            
            template = self._template_cache
            if template is None:
                return None
            
            # 임계값 (낮을수록 더 관대함)
            threshold = 0.6
            best_match = None
            best_val = 0
            
            # 다중 스케일 매칭 (0.9, 1.0, 1.1 - 속도와 정확도 균형)
            for scale in [1.0, 0.95, 1.05]:
                if scale != 1.0:
                    new_w = int(template.shape[1] * scale)
                    new_h = int(template.shape[0] * scale)
                    if new_w < 10 or new_h < 10:
                        continue
                    scaled = cv2.resize(template, (new_w, new_h))
                else:
                    scaled = template
                
                # 템플릿이 화면보다 크면 스킵
                if scaled.shape[0] > screenshot_gray.shape[0] or scaled.shape[1] > screenshot_gray.shape[1]:
                    continue
                
                # 템플릿 매칭
                result = cv2.matchTemplate(screenshot_gray, scaled, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_val:
                    best_val = max_val
                    best_match = max_loc
            
            # 임계값 이상이면 발견
            if best_val >= threshold and best_match:
                abs_x = self.mon_left + best_match[0]
                abs_y = self.mon_top + best_match[1]
                return (abs_x, abs_y)
            
            return None
            
        except Exception as e:
            print(f"이미지 검색 오류: {e}")
            return None


# 모듈 레벨 함수
def create_ticket_entry(callback=None):
    """TicketEntry 인스턴스 생성"""
    return TicketEntry(callback)
