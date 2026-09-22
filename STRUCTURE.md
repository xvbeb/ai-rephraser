# Структура AI Rephraser v2

- `main.py` — запуск Flask или PyQt6
- `desktop/gui.py` — QWebEngineView, тот же Flask backend
- `web/app.py` — фабрика приложения и конфигурация зависимостей
- `web/routes.py` — JSON API и SSE
- `core/llm/` — интерфейс провайдера и Gemini SDK
- `core/prompts/` — системные инструкции, тона, уточнения
- `core/schemas/` — Pydantic-схемы результата
- `core/service.py` — валидация и операции редактирования
- `core/conversations.py` — ограниченная история сессий в памяти
- `core/config.py`, `core/errors.py` — настройки и ошибки
- `static/`, `templates/` — существующий веб-интерфейс
- `tests/` — pytest с подменой Gemini
