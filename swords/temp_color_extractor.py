import cv2
import numpy as np
import os

print("Script started...")

def extract_color_samples(image_path, output_dir="seat_colors"):
    # 이미지 로드 (한글 경로 대응)
    img_array = np.fromfile(image_path, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 색상 정의 (색상명, HSV Lower, HSV Upper)
    # 대략적인 색상 범위 지정
    colors_to_find = [
        ("green", (40, 50, 50), (80, 255, 255)),   # 초록 (일반석?)
        ("blue", (100, 50, 50), (130, 255, 255)),  # 파랑 (VIP/R석?)
        ("purple", (130, 50, 50), (160, 255, 255)), # 보라 (OP석?)
        ("orange", (10, 50, 50), (25, 255, 255)),   # 주황
        ("red", (0, 50, 50), (10, 255, 255)),       # 빨강
    ]
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Extracting samples from {os.path.basename(image_path)}...")
    
    for color_name, lower, upper in colors_to_find:
        lower = np.array(lower, dtype="uint8")
        upper = np.array(upper, dtype="uint8")
        
        mask = cv2.inRange(hsv, lower, upper)
        
        # 노이즈 제거
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 컨투어 찾기
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        valid_sample_found = False
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 100: continue # 너무 작은 건 무시
            
            # Bounding Rect
            x, y, w, h = cv2.boundingRect(cnt)
            
            # 너무 길쭉하거나 이상한 형태 제외 (대략 정사각형 비율인 것 선호)
            aspect_ratio = float(w)/h
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                continue
                
            # 중앙 부분 안전하게 Crop (20x20)
            cx, cy = x + w//2, y + h//2
            half_size = 15
            
            # 이미지 범위 체크
            if (cy - half_size < 0) or (cy + half_size > img.shape[0]) or \
               (cx - half_size < 0) or (cx + half_size > img.shape[1]):
                continue
                
            sample = img[cy-half_size:cy+half_size, cx-half_size:cx+half_size]
            
            output_name = f"{color_name}_sample.png"
            output_path = os.path.join(output_dir, output_name)
            
            # 저장
            is_success, buffer = cv2.imencode(".png", sample)
            if is_success:
                with open(output_path, "wb") as f:
                    f.write(buffer)
                print(f"✅ Saved {output_name}")
                valid_sample_found = True
                break # 색상당 하나만 저장
        
        if not valid_sample_found:
            print(f"Colors for {color_name} not found.")

if __name__ == "__main__":
    # 사용자가 업로드한 이미지 경로
    target_image = r"C:\Users\Admin\.gemini\antigravity\brain\21b5465c-da58-4e1d-b8e2-dd5d3804654f\uploaded_image_1768978043869.png"
    extract_color_samples(target_image)
