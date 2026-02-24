# core/groq.py
import requests
from .config import GROQ_API_KEY

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

def call_groq(
    prompt: str,
    
    model: str = "llama-3.1-8b-instant", # mixtral-8x7b-32768
    max_tokens: int = 1200,
    temperature: float = 0.7
) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        resp = requests.post(GROQ_URL, headers=HEADERS, json=payload, timeout=25)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Ошибка Groq API: {str(e)}"