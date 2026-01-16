import sys
import os
import site
import time
import json
import re
import base64
from io import BytesIO

# -----------------------------------------------------------------------------
# 라이브러리 경로 설정 (Windows 환경 호환성)
# -----------------------------------------------------------------------------
try:
    user_sites = site.getusersitepackages()
    if isinstance(user_sites, str):
        user_sites = [user_sites]
    for path in user_sites:
        if os.path.exists(path) and path not in sys.path:
            sys.path.append(path)
            
    system_sites = site.getsitepackages()
    if isinstance(system_sites, str):
        system_sites = [system_sites]
    for path in system_sites:
        if os.path.exists(path) and path not in sys.path:
            sys.path.append(path)

except:
    pass

# 필수 라이브러리 임포트
try:
    import requests
    import pyautogui
    from PIL import ImageGrab
except ImportError as e:
    print(f"[Error] 필수 라이브러리가 없습니다: {e}")
    sys.exit(1)

# -----------------------------------------------------------------------------
# 설정
# -----------------------------------------------------------------------------
LM_STUDIO_URL = "http://localhost:12345/v1/chat/completions"
DEFAULT_MODEL = "local-model"

# 임시 폴더 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def encode_image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def analyze_screen_and_act(mon_x, mon_y, mon_w, mon_h, attempt):
    """
    화면을 캡처하고 VLM에게 분석 요청 후 행동 수행
    Return: (status, message)
    status: 'CONTINUE', 'DONE', 'LOADING', 'ERROR'
    """
    
    # 1. 화면 캡처
    bbox = (mon_x, mon_y, mon_x + mon_w, mon_y + mon_h)
    screenshot = ImageGrab.grab(bbox)
    
    # 디버깅용 저장 (temp 폴더 사용)
    debug_path = os.path.join(TEMP_DIR, f"popup_debug_step_{attempt}.png")
    screenshot.save(debug_path)
    
    width, height = screenshot.size
    base64_image = encode_image_to_base64(screenshot)
    
    # 2. VLM 프롬프트 구성
    # 좌표 (x, y)는 스크린샷 내의 상대 좌표여야 함
    prompt = f"""
    Analyze this screenshot ({width}x{height}) for specific UI elements to interact with.
    
    Tasks per Type:
    1. "CONFIRM": A popup asking "Proceed?" or "Confirm?". FIND the "확인" (Confirm) or "OK" button. Return its CENTER coordinates.
    2. "GUIDE": An informational popup. FIND the "닫기" (Close) or "X" button. Return its CENTER coordinates.
    3. "CAPTCHA": A security challenge. FIND the empty input box. Return the text in the captcha image and the input box CENTER coordinates.
    4. "LOADING": Screen is blank or has a spinner.
    5. "NONE": No obstructing popups.
    
    Response MUST be a JSON object:
    {{
      "type": "CONFIRM" | "GUIDE" | "CAPTCHA" | "LOADING" | "NONE",
      "text": "The text to type (for CAPTCHA) or button text found (for others)",
      "x": Integer (0-1000, normalized X coordinate of center),
      "y": Integer (0-1000, normalized Y coordinate of center)
    }}
    
    IMPORTANT: Provide Normalized Coordinates (0-1000). 
    x=0 is left, x=1000 is right. y=0 is top, y=1000 is bottom.
    """
    
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an AI agent that handles UI popups. Output valid JSON with normalized coordinates (0-1000)."
            },
            {
                "role": "user",
                "content": [
                    { "type": "text", "text": prompt },
                    { "type": "image_url", "image_url": { "url": f"data:image/png;base64,{base64_image}" } }
                ]
            }
        ],
        "temperature": 0.0,
        "max_tokens": 150
    }
    
    try:
        print(f"[{attempt}] Requesting VLM analysis (Normalizing Coords)...")
        response = requests.post(LM_STUDIO_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=10)
        
        if response.status_code != 200:
            print(f"VLM Error: {response.status_code}")
            return "ERROR", "VLM_FAIL"
            
        content = response.json()['choices'][0]['message']['content']
        print(f"[{attempt}] VLM Response: {content}")
        
        # JSON 파싱
        clean_content = re.sub(r'```json\s*', '', content)
        clean_content = re.sub(r'```', '', clean_content)
        data = json.loads(clean_content)
        
        p_type = data.get("type", "NONE").upper()
        p_text = data.get("text", "")
        norm_x = int(data.get("x", 0))
        norm_y = int(data.get("y", 0))
        
        # 좌표 변환 (0-1000 -> Pixel)
        rel_x = int(norm_x / 1000 * width)
        rel_y = int(norm_y / 1000 * height)
        
        # 절대 좌표 변환
        abs_x = mon_x + rel_x
        abs_y = mon_y + rel_y
        
        if p_type == "LOADING":
            print(">> Display is LOADING. Waiting...")
            return "LOADING", "Wait for load"
            
        elif p_type == "NONE":
            print(">> No popups detected.")
            return "DONE", "No popups"
            
        elif p_type in ["CONFIRM", "GUIDE"]:
            if rel_x > 0 and rel_y > 0:
                print(f">> Handling {p_type}: Clicking ({abs_x}, {abs_y})")
                pyautogui.click(abs_x, abs_y)
                return "CONTINUE", f"Clicked {p_type}"
            else:
                print(f">> Detect {p_type} but invalid coordinates.")
                return "CONTINUE", "Invalid Coords"
                
        elif p_type == "CAPTCHA":
            if p_text and rel_x > 0 and rel_y > 0:
                # 캡차 텍스트 정제
                captcha_str = "".join(e for e in p_text if e.isalnum())
                print(f">> Handling CAPTCHA: Type '{captcha_str}' at ({abs_x}, {abs_y})")
                
                pyautogui.click(abs_x, abs_y)
                time.sleep(0.1)
                pyautogui.write(captcha_str)
                time.sleep(0.1)
                pyautogui.press('enter')
                return "CONTINUE", "Solved Captcha"
            else:
                return "CONTINUE", "Invalid Captcha Data"
        
        else:
            print(f"Unknown type: {p_type}")
            return "CONTINUE", "Unknown Type"
            
    except Exception as e:
        print(f"Error: {e}")
        return "ERROR", str(e)


def run_popup_handler(mon_x, mon_y, mon_w, mon_h):
    max_retries = 12  # 최대 시도 횟수 (예: 12번 * 2초 = 약 24초 등)
    consecutive_none = 0
    target_none_count = 2 # NONE이 2번 연속 나와야 진짜 끝난 걸로 간주 (로딩 깜빡임 방지)
    
    print(f"Starting Popup Handler loop for region {mon_x},{mon_y},{mon_w},{mon_h}")
    
    captcha_detected = False
    loops_after_captcha = 0
    MAX_LOOPS_AFTER_CAPTCHA = 3

    for i in range(max_retries):
        # 캡차 처리 후 루프 횟수 제한 확인
        if captcha_detected:
            loops_after_captcha += 1
            if loops_after_captcha > MAX_LOOPS_AFTER_CAPTCHA:
                print(f"Force exiting: Reached {MAX_LOOPS_AFTER_CAPTCHA} loops after CAPTCHA.")
                break

        status, msg = analyze_screen_and_act(mon_x, mon_y, mon_w, mon_h, i+1)
        
        # 캡차 해결 여부 체크
        if msg == "Solved Captcha":
            captcha_detected = True

        if status == "DONE":
            consecutive_none += 1
            if consecutive_none >= target_none_count:
                print("All popups cleared. Exiting.")
                break
        elif status == "LOADING":
            consecutive_none = 0 # 로딩 중이면 카운트 리셋 (다시 기다림)
            time.sleep(1.0) # 로딩 중일 땐 좀 더 기다림
        else:
            # CONTINUE or ERROR
            consecutive_none = 0 # 뭔가를 처리했으면 카운트 리셋
            time.sleep(1.0) # 처리 후 UI 반영 대기
            
    print("Popup Handler finished.")

if __name__ == "__main__":
    # 인자: mon_x mon_y mon_w mon_h
    if len(sys.argv) < 5:
        # 테스트용 디폴트 (인자 없으면 0,0,1920,1080)
        # print("Usage: python popup_handler.py <x> <y> <w> <h>")
        run_popup_handler(0, 0, 1920, 1080)
    else:
        x = int(sys.argv[1])
        y = int(sys.argv[2])
        w = int(sys.argv[3])
        h = int(sys.argv[4])
        run_popup_handler(x, y, w, h)
