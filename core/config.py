from dotenv import load_dotenv
import os

load_dotenv()

# Константы
PORT = int(os.getenv("PORT", 5000))
BASE_URL = f"http://127.0.0.1:{PORT}"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Если нужно — другие настройки позже
DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"