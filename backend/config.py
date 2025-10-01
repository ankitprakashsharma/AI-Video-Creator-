import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "static/uploads")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

os.makedirs(UPLOAD_DIR, exist_ok=True)
