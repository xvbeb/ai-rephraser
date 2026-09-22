import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
from werkzeug.serving import BaseWSGIServer

from core.config import PORT, HOST, BASE_URL
from web.app import app as flask_app


def run_local_server(server: BaseWSGIServer | None = None) -> None:
    if server is not None:
        server.serve_forever()
    else:
        flask_app.run(debug=False, use_reloader=False, host=HOST, port=PORT, threaded=True)


def run_desktop(server_url: str = BASE_URL) -> None:
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
