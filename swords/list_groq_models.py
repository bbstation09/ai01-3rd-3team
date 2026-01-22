import os
import requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")  # 환경변수에서 로드
GROQ_API_URL = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(GROQ_API_URL, headers=headers)
    if response.status_code == 200:
        models = response.json()['data']
        print(f"Found {len(models)} models:")
        for model in models:
            print(f"- {model['id']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Exception: {e}")
