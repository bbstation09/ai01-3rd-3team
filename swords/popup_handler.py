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
# -----------------------------------------------------------------------------
# 설정
# -----------------------------------------------------------------------------
# [설정] 사용할 AI 제공자 선택: "LM_STUDIO" 또는 "GROQ"
# 다시 LM Studio로 돌아가려면 이 값을 "LM_STUDIO"로 변경하세요.
# USE_PROVIDER = "GROQ" 
USE_PROVIDER = "LM_STUDIO"

# LM Studio 설정
LM_STUDIO_CONFIG = {
    "URL": "http://localhost:12345/v1/chat/completions",
    "MODEL": "local-model",
    "API_KEY": "lm-studio" # LM Studio는 보통 키가 필요 없지만 포맷 유지
}

# Groq 설정 (Llama 4 Scout 비전 모델 사용)
# API 키는 환경변수에서 가져오거나 여기에 직접 입력하세요.
GROQ_CONFIG = {
    "URL": "https://api.groq.com/openai/v1/chat/completions",
    "MODEL": "meta-llama/llama-4-scout-17b-16e-instruct",  # Llama 4 Scout 비전 모델
    "API_KEY": os.environ.get("GROQ_API_KEY", "").strip()  # 환경변수에서 로드
}

# 임시 폴더 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def encode_image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def handle_seat_selection(mon_x, mon_y, mon_w, mon_h):
    """
    좌석 선택 화면 처리 함수
    - 좌석이 보이지 않으면 확대 시도
    - 중앙 우선으로 좋은 좌석 5개 후보 분석
    - 순차적으로 클릭하여 선택 시도
    - 5개 모두 실패 시 새로운 5개 후보 요청
    - 선택 성공 시 결제 버튼 클릭
    """
    print("=" * 50)
    print("좌석선택 자동화 시작")
    print("=" * 50)
    
    max_rounds = 5  # 최대 5라운드 (25개 좌석 시도)
    max_zoom_attempts = 3  # 최대 확대 시도 횟수
    zoom_attempts = 0
    
    for round_num in range(max_rounds):
        print(f"\n[라운드 {round_num + 1}] 좌석 후보 5개 분석 중...")
        
        # 화면 캡처
        bbox = (mon_x, mon_y, mon_x + mon_w, mon_y + mon_h)
        screenshot = ImageGrab.grab(bbox)
        width, height = screenshot.size
        base64_image = encode_image_to_base64(screenshot)
        
        # VLM으로 좌석 5개 후보 요청
        seats = get_seat_candidates(base64_image, width, height)
        
        if not seats:
            print(">> 좌석 후보를 찾을 수 없습니다.")
            
            # 좌석이 보이지 않으면 확대 시도
            if zoom_attempts < max_zoom_attempts:
                print(f">> 확대 시도 ({zoom_attempts + 1}/{max_zoom_attempts})...")
                zoom_in_seat_map(mon_x, mon_y, mon_w, mon_h)
                zoom_attempts += 1
                time.sleep(0.5)
                continue
            else:
                print(">> 최대 확대 시도 횟수 초과. 계속 진행...")
            
            time.sleep(1)
            continue
        
        print(f">> {len(seats)}개 좌석 후보 발견: {seats}")
        
        # 각 좌석 클릭 시도
        for i, seat in enumerate(seats):
            norm_x = seat.get("x", 0)
            norm_y = seat.get("y", 0)
            
            # 정규화 검증
            if norm_x > 1.0:
                norm_x = norm_x / width
            if norm_y > 1.0:
                norm_y = norm_y / height
            
            abs_x = mon_x + int(norm_x * width)
            abs_y = mon_y + int(norm_y * height)
            
            print(f">> [{i+1}/5] 좌석 클릭: ({abs_x}, {abs_y})")
            pyautogui.click(abs_x, abs_y)
            time.sleep(0.5)
            
            # 대화창 처리 (좌석 선택 실패 시 Enter 필요할 수 있음)
            pyautogui.press('enter')
            time.sleep(0.3)
            
            # 선택 성공 여부 확인
            if check_seat_selected(mon_x, mon_y, mon_w, mon_h):
                print(">> 좌석 선택 성공!")
                
                # 결제 버튼 클릭
                click_payment_button(mon_x, mon_y, mon_w, mon_h)
                return True
        
        print(f">> 라운드 {round_num + 1} 좌석 모두 실패. 다음 라운드...")
        time.sleep(0.5)
    
    print(">> 모든 라운드 실패. 좌석 선택 종료.")
    return False


def zoom_in_seat_map(mon_x, mon_y, mon_w, mon_h):
    """
    좌석 맵 영역을 확대 (마우스 휠 사용)
    - 화면 중앙 부분에서 스크롤 업으로 확대
    """
    # 좌석 맵이 있을 것으로 예상되는 영역 중앙으로 이동
    # 보통 화면의 왼쪽~중앙 영역
    target_x = mon_x + int(mon_w * 0.3)
    target_y = mon_y + int(mon_h * 0.5)
    
    print(f">> 확대: 마우스를 ({target_x}, {target_y})로 이동 후 휠 업")
    pyautogui.moveTo(target_x, target_y)
    time.sleep(0.2)
    
    # 마우스 휠 업 (확대)
    pyautogui.scroll(3)  # 양수 = 위로 스크롤 = 확대
    time.sleep(0.3)


def get_seat_candidates(base64_image, width, height):
    """VLM으로 좌석 5개 후보 좌표 반환"""
    
    if USE_PROVIDER == "GROQ":
        target_url = GROQ_CONFIG["URL"]
        target_model = GROQ_CONFIG["MODEL"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_CONFIG['API_KEY']}"
        }
    else:
        target_url = LM_STUDIO_CONFIG["URL"]
        target_model = LM_STUDIO_CONFIG["MODEL"]
        headers = {"Content-Type": "application/json"}
    
    prompt = f"""Screenshot size: {width}x{height} pixels.

This page shows a seat selection interface.
Look for the seat map area with:
- "STAGE" text 
- A seating grid with small colored squares or boxes representing seats
- Seat type labels or sections

Seat colors:
- COLORED small squares/boxes (blue, green, orange, pink, etc.) = AVAILABLE (can be clicked)
- WHITE/GRAY/EMPTY = NOT available

Find 5 AVAILABLE seats (colored squares/boxes) in the seat map.
Return the CENTER coordinates of each colored seat element.

CRITICAL: Coordinates MUST be 0.0-1.0 normalized relative to the ENTIRE screenshot!
- x=0.0 is left edge, x=1.0 is right edge
- y=0.0 is top edge, y=1.0 is bottom edge

JSON only:
{{"seats": [{{"x": 0.xx, "y": 0.xx}}, {{"x": 0.xx, "y": 0.xx}}, {{"x": 0.xx, "y": 0.xx}}, {{"x": 0.xx, "y": 0.xx}}, {{"x": 0.xx, "y": 0.xx}}]}}"""

    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": "You are a JSON API. Output ONLY valid JSON."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]}
        ],
        "temperature": 0.0,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(target_url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            print(f"VLM Error: {response.status_code}")
            return []
        
        content = response.json()['choices'][0]['message']['content']
        print(f">> VLM Raw Response: {content[:500]}")  # Debug output
        clean_content = re.sub(r'```json\s*', '', content)
        clean_content = re.sub(r'```', '', clean_content)
        data = json.loads(clean_content)
        
        return data.get("seats", [])
    except Exception as e:
        print(f"Error getting seat candidates: {e}")
        return []


def check_seat_selected(mon_x, mon_y, mon_w, mon_h):
    """좌석이 선택되었는지 확인 (선택 내역에 좌석 추가 여부)"""
    
    bbox = (mon_x, mon_y, mon_x + mon_w, mon_y + mon_h)
    screenshot = ImageGrab.grab(bbox)
    width, height = screenshot.size
    base64_image = encode_image_to_base64(screenshot)
    
    if USE_PROVIDER == "GROQ":
        target_url = GROQ_CONFIG["URL"]
        target_model = GROQ_CONFIG["MODEL"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_CONFIG['API_KEY']}"
        }
    else:
        target_url = LM_STUDIO_CONFIG["URL"]
        target_model = LM_STUDIO_CONFIG["MODEL"]
        headers = {"Content-Type": "application/json"}
    
    prompt = """Check if a seat has been selected.
Look for "선택 내역" section on the right side.
If there is seat information (row/seat number) shown, a seat is selected.

JSON only:
{"selected": true} or {"selected": false}"""
    
    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": "You are a JSON API. Output ONLY valid JSON."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]}
        ],
        "temperature": 0.0,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(target_url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return False
        
        content = response.json()['choices'][0]['message']['content']
        clean_content = re.sub(r'```json\s*', '', content)
        clean_content = re.sub(r'```', '', clean_content)
        data = json.loads(clean_content)
        
        return data.get("selected", False)
    except Exception as e:
        print(f"Error checking seat selection: {e}")
        return False


def click_payment_button(mon_x, mon_y, mon_w, mon_h):
    """결제 하기 버튼 클릭"""
    
    bbox = (mon_x, mon_y, mon_x + mon_w, mon_y + mon_h)
    screenshot = ImageGrab.grab(bbox)
    width, height = screenshot.size
    base64_image = encode_image_to_base64(screenshot)
    
    if USE_PROVIDER == "GROQ":
        target_url = GROQ_CONFIG["URL"]
        target_model = GROQ_CONFIG["MODEL"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_CONFIG['API_KEY']}"
        }
    else:
        target_url = LM_STUDIO_CONFIG["URL"]
        target_model = LM_STUDIO_CONFIG["MODEL"]
        headers = {"Content-Type": "application/json"}
    
    prompt = f"""Screenshot size: {width}x{height} pixels.

Find the "결제 하기" (Payment/Checkout) button.
Return its CENTER coordinates.

CRITICAL: Coordinates MUST be 0.0-1.0 normalized!

JSON only:
{{"x": 0.xx, "y": 0.xx}}"""
    
    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": "You are a JSON API. Output ONLY valid JSON."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]}
        ],
        "temperature": 0.0,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(target_url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            print(f"VLM Error finding payment button: {response.status_code}")
            return
        
        content = response.json()['choices'][0]['message']['content']
        clean_content = re.sub(r'```json\s*', '', content)
        clean_content = re.sub(r'```', '', clean_content)
        data = json.loads(clean_content)
        
        norm_x = float(data.get("x", 0))
        norm_y = float(data.get("y", 0))
        
        if norm_x > 1.0:
            norm_x = norm_x / width
        if norm_y > 1.0:
            norm_y = norm_y / height
        
        abs_x = mon_x + int(norm_x * width)
        abs_y = mon_y + int(norm_y * height)
        
        print(f">> 결제 버튼 클릭: ({abs_x}, {abs_y})")
        pyautogui.click(abs_x, abs_y)
        
    except Exception as e:
        print(f"Error clicking payment button: {e}")

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
    
    # 2. 설정에 따른 요청 준비
    if USE_PROVIDER == "GROQ":
        target_url = GROQ_CONFIG["URL"]
        target_model = GROQ_CONFIG["MODEL"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_CONFIG['API_KEY']}"
        }
    else: # LM_STUDIO
        target_url = LM_STUDIO_CONFIG["URL"]
        target_model = LM_STUDIO_CONFIG["MODEL"]
        headers = {
            "Content-Type": "application/json"
        }

    # 3. VLM 프롬프트 구성 (0.0-1.0 정규화 방식)
    prompt = f"""Screenshot size: {width}x{height} pixels.

Find popup type and return JSON only.

Types:
- CONFIRM: Has "확인"/"OK" button -> x,y = button center
- GUIDE: Has "닫기"/"X" button -> x,y = button center
- CAPTCHA: Has distorted text image + input field
  1. READ the distorted characters (e.g., "RVRMOJ") -> put in "text"
  2. FIND the center of INPUT FIELD (empty box with "보 안 문 자" text inside)
     This input field is BELOW the distorted image, where user will type the answer
  3. x,y = CENTER of this INPUT FIELD (not the image, not the button!)
- SEAT_SELECTION: Seat selection page with:
  * "STAGE" text and type of seats
  * Grid of small squares representing seats or boxed areas 
  -> x,y = 0.5, 0.5 (center, not used)
- LOADING: Loading screen
- NONE: No popup

CRITICAL: x and y MUST be between 0.0 and 1.0!
- x=0.0 means left edge, x=0.5 means horizontal center, x=1.0 means right edge
- y=0.0 means top edge, y=0.5 means vertical center, y=1.0 means bottom edge

Output format (JSON only, no explanation):
{{"type":"...","text":"...","x":0.xx,"y":0.xx}}"""
    
    payload = {
        "model": target_model,
        "messages": [
            {
                "role": "system",
                "content": "You are a JSON API. Output ONLY valid JSON. Never include explanations, markdown, or code blocks."
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
        print(f"[{attempt}] Requesting VLM analysis to {USE_PROVIDER} (Normalizing Coords)...")
        # 디버깅: 페이로드 구조 확인 (이미지는 길이만 출력)
        debug_payload = payload.copy()
        if 'messages' in debug_payload:
            # 깊은 복사나 구조 변경 필요 없이, 로깅용으로만 살짝 보여주기
            pass 
        # print(f"DEBUG Payload keys: {payload.keys()}")
        
        response = requests.post(target_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"VLM Error: {response.status_code}")
            print(f"Response Body: {response.text}")
            return "ERROR", "VLM_FAIL"
            
        content = response.json()['choices'][0]['message']['content']
        print(f"[{attempt}] VLM Response: {content}")
        
        # JSON 파싱
        clean_content = re.sub(r'```json\s*', '', content)
        clean_content = re.sub(r'```', '', clean_content)
        data = json.loads(clean_content)
        
        p_type = data.get("type", "NONE").upper()
        p_text = data.get("text", "")
        raw_x = float(data.get("x", 0))
        raw_y = float(data.get("y", 0))
        
        # 정규화 검증: 값이 1.0보다 크면 픽셀 좌표로 간주하고 정규화
        if raw_x > 1.0:
            norm_x = raw_x / width
            print(f">> Warning: x={raw_x} > 1.0, assuming pixel coords. Normalized to {norm_x:.3f}")
        else:
            norm_x = raw_x
            
        if raw_y > 1.0:
            norm_y = raw_y / height
            print(f">> Warning: y={raw_y} > 1.0, assuming pixel coords. Normalized to {norm_y:.3f}")
        else:
            norm_y = raw_y
        
        # 좌표 변환 (0.0-1.0 -> Pixel)
        rel_x = int(norm_x * width)
        rel_y = int(norm_y * height)
        
        # 절대 좌표 변환 (모니터 오프셋 추가)
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
                print(f">> CAPTCHA Debug: norm_x={norm_x}, norm_y={norm_y}")
                print(f">> CAPTCHA Debug: width={width}, height={height}")
                print(f">> CAPTCHA Debug: rel_x={rel_x}, rel_y={rel_y}")
                print(f">> Handling CAPTCHA: Type '{captcha_str}' at ({abs_x}, {abs_y})")
                
                pyautogui.click(abs_x, abs_y)
                time.sleep(0.1)
                pyautogui.write(captcha_str)
                time.sleep(0.1)
                pyautogui.press('enter')
                return "CONTINUE", "Solved Captcha"
            else:
                return "CONTINUE", "Invalid Captcha Data"
        
        elif p_type == "SEAT_SELECTION":
            print(">> 좌석선택 화면 감지!")
            handle_seat_selection(mon_x, mon_y, mon_w, mon_h)
            return "DONE", "Seat Selection"
        
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
