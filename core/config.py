"""Environment configuration shared by web and desktop entry points."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

PORT = int(os.getenv("PORT", "5000"))
HOST = os.getenv("HOST", "127.0.0.1")
BASE_URL = f"http://127.0.0.1:{PORT}"
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"


def app_settings() -> dict:
    return {
        "SECRET_KEY": os.getenv("SECRET_KEY") or None,
        "APP_ENV": os.getenv("APP_ENV", "development"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "AI_MODEL": os.getenv("AI_MODEL", "gemini-2.5-flash"),
        "AI_TIMEOUT_MS": int(os.getenv("AI_TIMEOUT_MS", "30000")),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": os.getenv("APP_ENV") == "production",
        "MAX_CONTENT_LENGTH": 100_000,
    }
