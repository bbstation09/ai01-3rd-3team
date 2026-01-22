"""
VLM Handler Module
VLM(Vision Language Model) API 호출을 위한 공통 함수들
"""

import os
import re
import json
import base64
import requests
import pyautogui
from io import BytesIO
from PIL import ImageGrab


def click_and_restore(x: int, y: int, delay: float = 0.0):
    """
    클릭 후 마우스를 원래 위치로 복원 (빠른 원자적 동작)
    
    Args:
        x: 클릭할 X 좌표
        y: 클릭할 Y 좌표
        delay: 클릭 전 대기 시간 (초)
    """
    import time
    
    # 현재 마우스 위치 저장 (시작 시점)
    orig_x, orig_y = pyautogui.position()
    
    # 일시적으로 기본 대기시간 비활성화 (더 빠른 동작)
    original_pause = pyautogui.PAUSE
    pyautogui.PAUSE = 0
    
    try:
        # 빠른 클릭 (이동 + 클릭 한번에)
        if delay > 0:
            time.sleep(delay)
        pyautogui.click(x, y)
        
        # 원래 위치로 즉시 복원
        pyautogui.moveTo(orig_x, orig_y)
    finally:
        # 원래 대기시간 복원
        pyautogui.PAUSE = original_pause

# -----------------------------------------------------------------------------
# VLM 설정
# -----------------------------------------------------------------------------
USE_PROVIDER = "LM_STUDIO"  # "LM_STUDIO" 또는 "GROQ"

LM_STUDIO_CONFIG = {
    "URL": "http://localhost:12345/v1/chat/completions",
    "MODEL": "local-model",
    "API_KEY": "lm-studio"
}

GROQ_CONFIG = {
    "URL": "https://api.groq.com/openai/v1/chat/completions",
    "MODEL": "meta-llama/llama-4-scout-17b-16e-instruct",
    "API_KEY": os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE").strip()
}


def encode_image_to_base64(image):
    """이미지를 base64 문자열로 인코딩"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def get_vlm_config():
    """현재 설정된 VLM 제공자 정보 반환"""
    if USE_PROVIDER == "GROQ":
        return {
            "url": GROQ_CONFIG["URL"],
            "model": GROQ_CONFIG["MODEL"],
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_CONFIG['API_KEY']}"
            }
        }
    else:
        return {
            "url": LM_STUDIO_CONFIG["URL"],
            "model": LM_STUDIO_CONFIG["MODEL"],
            "headers": {"Content-Type": "application/json"}
        }


def call_vlm(prompt: str, base64_image: str, max_tokens: int = 150, temperature: float = 0.0) -> dict:
    """
    VLM API 호출
    
    Args:
        prompt: 텍스트 프롬프트
        base64_image: base64 인코딩된 이미지
        max_tokens: 최대 토큰 수
        temperature: 응답 다양성 (0.0 = 결정적)
    
    Returns:
        파싱된 JSON 응답 또는 빈 딕셔너리
    """
    config = get_vlm_config()
    
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "system",
                "content": "You are a JSON API. Output ONLY valid JSON. Never include explanations, markdown, or code blocks."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(config["url"], headers=config["headers"], json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"VLM Error: {response.status_code}")
            print(f"Response: {response.text}")
            return {}
        
        content = response.json()['choices'][0]['message']['content']
        print(f">> VLM Raw Response: {content[:300]}")
        
        # JSON 정리 및 파싱
        clean_content = re.sub(r'```json\s*', '', content)
        clean_content = re.sub(r'```', '', clean_content)
        return json.loads(clean_content)
        
    except Exception as e:
        print(f"VLM Error: {e}")
        return {}


def capture_screen(mon_x: int, mon_y: int, mon_w: int, mon_h: int):
    """화면 영역 캡처"""
    bbox = (mon_x, mon_y, mon_x + mon_w, mon_y + mon_h)
    return ImageGrab.grab(bbox)
