# web/app.py
from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__,
            template_folder='../templates',          # указываем путь относительно корня проекта
            static_folder='../static')               # то же самое для static

# секретный ключ для сессий (в продакшене лучше в .env)
app.secret_key = os.getenv("SECRET_KEY", 'Slognone1337_very_random_change_me')

# Импортируем роуты после создания app (важно!)
from .routes import *   # импортируем всё из routes.py