# desktop/app_desk.py

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import sys
import threading

from core.config import PORT, BASE_URL
from web.app import app as flask_app

def run_local_server():
    """Запуск Flask-сервера в отдельном потоке"""
    flask_app.run(
        debug=False,
        use_reloader=False,
        host="0.0.0.0",
        port=PORT,
        threaded=True
    )

def run_desktop(server_url=BASE_URL):
    """Запуск десктопного окна"""
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("AI Переписыватель — Neon Desktop")
    window.setGeometry(100, 100, 1000, 800)
    window.setMinimumSize(800, 600)

    browser = QWebEngineView()
    window.setCentralWidget(browser)
    browser.setUrl(QUrl(server_url))

    window.show()
    sys.exit(app.exec())