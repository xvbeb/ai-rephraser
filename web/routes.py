# web/routes.py
from flask import render_template, request, jsonify, session

# ──── вот эти две строки ────
from .app import app                     # ← импортируем app из этого же пакета web/

from core.config import GROQ_API_KEY
from core.groq import call_groq
from core.prompts import tone_descriptions, build_rephrase_prompt

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

@app.route("/")
def index():
    return render_template("index.html")


# /rephrase — теперь возвращает ТОЛЬКО исправленный текст
@app.route("/rephrase", methods=["POST"])
def rephrase():
    data = request.get_json()
    text = data.get("text", "").strip()
    tone = data.get("tone", "neutral")

    if not text:
        return jsonify({"error": "Текст пустой"}), 400

    prompt = build_rephrase_prompt(text, tone)

    full_response = call_groq(prompt)

    # Парсим ответ — берём только "Исправленный текст:"
    try:
        corrected_text = full_response.split("Исправленный текст:")[1].split("Объяснение изменений:")[0].strip()
    except:
        corrected_text = full_response  # если парсинг сломался — возвращаем всё

    # Добавляем полный ответ в чат-историю как первое сообщение от ИИ
    if "chat_history" not in session:
        session["chat_history"] = []

    session["chat_history"].append({"role": "user", "content": text})
    session["chat_history"].append({"role": "assistant", "content": full_response})
    session.modified = True

    return jsonify({"result": corrected_text})  # только исправленный текст


@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "chat_history" not in session:
        session["chat_history"] = []

    if request.method == "POST":
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if user_message:
            session["chat_history"].append({"role": "user", "content": user_message})

            tone = data.get("tone", "neutral")  # можно передать тон из фронта
            tone_desc = tone_descriptions.get(tone, "Нейтральный тон по умолчанию.")

            system_prompt = f"""
Ты эксперт по стилистике и грамматике.
Текущий тон: {tone_desc}
Ты помнишь ВСЮ предыдущую беседу.
Всегда отвечай с учётом всей истории сообщений.
Если пользователь спрашивает о чём-то из прошлого — ссылайся на это явно.
"""

            messages = [
                {"role": "system", "content": system_prompt}
            ] + session["chat_history"]

            full_answer = call_groq(
                prompt="\n".join([m["content"] for m in messages]),  # вся история
                temperature=0.7,
                max_tokens=1500
            )

            session["chat_history"].append({"role": "assistant", "content": full_answer})
            session.modified = True

    return jsonify({"history": session["chat_history"]})


# Очистка чата (уже добавляли)
@app.route("/chat/clear", methods=["POST"])
def clear_chat():
    session.pop("chat_history", None)
    return jsonify({"status": "cleared"})

# Если хочешь — можно вынести tone_descriptions в отдельный эндпоинт
@app.route("/tones", methods=["GET"])
def get_tones():
    return jsonify({"tones": list(tone_descriptions.keys())})