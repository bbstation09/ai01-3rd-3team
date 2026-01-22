import cv2
import numpy as np
import os
import glob

class ColorManager:
    def __init__(self, color_dir="seat_colors"):
        self.color_dir = color_dir
        self.target_colors = []  # [(lower, upper), ...]
    
    def load_colors(self, selected_color="All Colors"):
        """저장된 이미지들에서 색상 범위 로드
        
        Args:
            selected_color: "All Colors" 또는 특정 색상 파일명 (확장자 제외)
        """
        self.target_colors = []
        
        if not os.path.exists(self.color_dir):
            os.makedirs(self.color_dir, exist_ok=True)
            return []
        
        # 파일 목록 결정
        if selected_color == "All Colors":
            # 모든 색상 파일 로드
            extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp']
            files = []
            for ext in extensions:
                files.extend(glob.glob(os.path.join(self.color_dir, ext)))
        else:
            # 특정 색상 파일만 로드
            files = []
            for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                path = os.path.join(self.color_dir, selected_color + ext)
                if os.path.exists(path):
                    files.append(path)
                    break
            
        print(f"[ColorManager] Loading {len(files)} color(s): {selected_color}")
        
        for f in files:
            try:
                # 한글 경로 지원을 위한 imdecode 사용
                img_array = np.fromfile(f, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
                if img is None:
                    continue
                
                # BGR to HSV
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                
                # 이미지의 중앙 부분만 샘플링 (10x10)
                h, w = hsv.shape[:2]
                cx, cy = w//2, h//2
                sample = hsv[max(0, cy-5):min(h, cy+5), max(0, cx-5):min(w, cx+5)]
                
                if sample.size == 0:
                    sample = hsv # 너무 작으면 전체 사용
                
                # 평균 색상 계산
                mean_color = np.mean(sample.reshape(-1, 3), axis=0)
                
                # 범위 설정 (H: ±10, S: ±40, V: ±50) - 유연하게
                H, S, V = mean_color
                
                lower = np.array([max(0, H-10), max(30, S-40), max(30, V-50)])
                upper = np.array([min(180, H+10), min(255, S+40), min(255, V+50)])
                
                self.target_colors.append((lower, upper))
                print(f"  Loaded: {os.path.basename(f)} -> HSV({int(H)},{int(S)},{int(V)})")
                
            except Exception as e:
                print(f"  Error loading {f}: {e}")
                
        return self.target_colors

    def get_mask(self, hsv_image):
        """이미지에서 타겟 색상 마스크 생성"""
        if not self.target_colors:
            # 색상 설정이 없으면: 채도가 있고 적당히 밝은 모든 색 (흰색/회색 제외)
            # S > 30 (무채색 제외), V < 250 (완전 흰색 제외)
            lower_white = np.array([0, 0, 200]) # 매우 밝은 회색~흰색
            
            # 1. 전체 마스크 (모든 것)
            # mask = np.ones(hsv_image.shape[:2], dtype="uint8") * 255
            
            # 대안: 채도가 있는 것들만 (Colorful)
            lower_color = np.array([0, 30, 50])
            upper_color = np.array([180, 255, 255])
            mask = cv2.inRange(hsv_image, lower_color, upper_color)
            
            return mask
        
        # 설정된 색상들의 합집합
        mask = np.zeros(hsv_image.shape[:2], dtype="uint8")
        for lower, upper in self.target_colors:
            color_mask = cv2.inRange(hsv_image, lower, upper)
            mask = cv2.bitwise_or(mask, color_mask)
            
        return mask
