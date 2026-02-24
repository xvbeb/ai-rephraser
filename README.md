# AI Переписыватель | Neon Edition

Веб-приложение + десктопная версия для переписывания текста с помощью ИИ (Groq API).  
Поддерживает разные тона (нейтральный, формальный, bydlo, креативный и т.д.), чат для уточнений и тёмную/светлую тему.

## Возможности

- Переписывание текста в выбранном тоне
- Чат с ИИ для доработки и споров
- Десктопная версия на PyQt6 (локальный сервер или подключение к удалённому)
- Неоновый дизайн с поддержкой светлой и тёмной темы
- Копирование результата в буфер обмена

## Технологии

- Backend: Flask
- Frontend: HTML, CSS, JavaScript
- Десктоп: PyQt6 + QWebEngineView
- ИИ: Groq API (Llama-3.1-8b-instant / другие модели)
- Telegram-бот (в разработке)

## Установка и запуск

1. Клонируй репозиторий
```bash
git clone https://github.com/xbeb/ai-rephraser.git
cd ai-rephraser

2. Создай виртуальное окружение

python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

3. Установи зависимости

pip install -r requirements.txt

4. Скопируй .env.example → .env и заполни ключи

cp .env.example .env
# открой .env и вставь GROQ_API_KEY

5. Запуск

С GUI (ПО УМОЛЧАНИЮ)

* python main.py

Только сервер (без окна)

python main.py --no-gui

Структура проекта

core/ — общая логика (конфиг, groq-клиент, промпты)
web/ — Flask приложение
desktop/ — PyQt6 интерфейс
bot/ — Telegram-бот (в разработке)
static/ — css, js
templates/ — HTML

Лицензия
MIT License — делай что хочешь, главное укажи автора, если будешь форкать/распространять.
text