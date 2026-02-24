Напоминание о текущей структуре проекта (февраль 2026):
- корневой main.py — точка входа (лаунчер)
- desktop/gui.py — PyQt6 + логика запуска десктопа
- web/app.py + web/routes.py — Flask
- core/config.py, core/groq.py, core/prompts.py — общая логика
- bot/bot.py — Telegram-бот (пока в зачатке)
