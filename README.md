# ⚡ AI Rephraser

AI-сервіс для редагування та перефразування тексту за допомогою **Google Gemini**.

Дозволяє виправляти текст у різних стилях, пояснює внесені зміни та підтримує подальше редагування через чат з AI.

## ✨ Можливості

- Перефразування та виправлення тексту через Gemini
- Кілька стилів: нейтральний, діловий, професійний, креативний та інші
- Structured Output із валідацією через Pydantic
- Пояснення внесених змін
- Чат для подальшого редагування
- Streaming відповідей через SSE
- Збереження контексту діалогу
- Обробка помилок та таймаутів Gemini API
- Web та Desktop версії

## 🕒 Цікавий факт

Перша публічна версія **AI Rephraser** з'явилася на GitHub **24 лютого 2026 року**.

**31 березня 2026 року** Telegram представив власний AI Text Editor із дуже схожою ідеєю: виправлення тексту, переписування в різних стилях та AI-редагування прямо перед відправленням повідомлення.

Тобто перша версія цього проєкту була опублікована приблизно за **5 тижнів до появи аналогічної функції в Telegram**.

## 🧠 AI-архітектура

Робота з LLM винесена в окремий шар:

```text
Flask API
    ↓
RephraseService
    ↓
LLMProvider
    ↓
GeminiProvider
    ↓
Google Gemini API
```

`LLMProvider` відокремлює бізнес-логіку від конкретного AI-провайдера.

Для основного перефразування Gemini повертає структуровану відповідь, яка додатково перевіряється через **Pydantic**. Чат працює у streaming-режимі через **Server-Sent Events (SSE)**.

## 🛠 Стек

- Python
- Flask
- Google Gemini API
- Pydantic
- PyQt6
- HTML / CSS / JavaScript
- pytest

## 📁 Структура

```text
core/
├── llm/            # LLM abstraction + Gemini
├── prompts/        # системні промпти
├── schemas/        # Pydantic-схеми
├── service.py      # бізнес-логіка
└── conversations.py

web/                # Flask API
desktop/            # PyQt6
static/             # Frontend
templates/
tests/
```

## 🚀 Запуск

```bash
git clone https://github.com/xvbeb/ai-rephraser.git
cd ai-rephraser

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Додай Gemini API key у `.env`:

```env
GEMINI_API_KEY=your_api_key
```

Web:

```bash
python main.py --no-gui
```

Desktop:

```bash
python main.py
```

## 🧪 Тести

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Тести перевіряють structured output, streaming, conversation state, помилки провайдера, таймаути та валідацію API.

## 📄 License

MIT