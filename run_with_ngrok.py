import os
import uvicorn
from pyngrok import ngrok, conf
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_ngrok():
    # Get token from environment variable
    token = os.getenv("NGROK_AUTHTOKEN")
    
    if token:
        print(f"Adding auth token: {token[:4]}...")
        # Set auth token
        conf.get_default().auth_token = token
    else:
        print("Warning: NGROK_AUTHTOKEN not found in .env, ngrok may fail if account is required.")

    # Start ngrok tunnel
    # Note: If you have a paid plan you can specify domain in options
    public_url = ngrok.connect(8000).public_url
    print(f"\n==========================================")
    print(f"Ngrok Tunnel URL: {public_url}")
    print(f"You can access the site at: {public_url}")
    print(f"==========================================\n")

if __name__ == "__main__":
    # Start ngrok before app
    start_ngrok()
    
    # Run FastAPI app
    # Assumption: main.py has an 'app' instance
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
