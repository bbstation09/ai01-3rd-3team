import os
import base64
import requests
from io import BytesIO
from PIL import ImageGrab, Image

# [설정] Groq API 키 및 모델
# [설정] Groq API 키 및 모델 (환경변수에서 로드)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")  # 환경변수에서 로드
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Groq에서 지원하는 비전 모델 (2025년 기준)
# - meta-llama/llama-4-scout-17b-16e-instruct (NEW - Llama 4 Scout)
# - meta-llama/llama-4-maverick-17b-128e-instruct (NEW - Llama 4 Maverick)
MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"

def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def test_vlm():
    print("1. Taking a screenshot for testing...")
    # 전체 화면 대신 작게 캡처 (0,0 에서 500x500)
    screenshot = ImageGrab.grab(bbox=(0, 0, 500, 500))
    base64_image = encode_image(screenshot)
    print(f"   Image captured & encoded (Length: {len(base64_image)})")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What is in this image? Describe briefly."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 300
    }

    print(f"2. Sending request to Groq ({MODEL_NAME})...")
    print(f"   URL: {GROQ_API_URL}")

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        
        print(f"3. Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            print("\n✅ Success! VLM Output:")
            print("-" * 40)
            print(content)
            print("-" * 40)
        else:
            print("\n❌ Error! Response Body:")
            print(response.text)

    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")

if __name__ == "__main__":
    test_vlm()
