# main.py  (корень проекта)
import argparse
import sys
import threading
import time

from desktop.gui import run_desktop, run_local_server  # импортируем функции

def main():
    parser = argparse.ArgumentParser(description="AI Переписыватель Neon")
    parser.add_argument("--remote-url", help="Подключиться к удалённому серверу вместо локального")
    parser.add_argument("--no-gui", action="store_true", help="Запустить только сервер без GUI")
    args = parser.parse_args()

    # Запускаем локальный сервер, если НЕ указан удалённый URL
    if not args.remote_url:
        print("Запускаю локальный Flask-сервер...")
        server_thread = threading.Thread(target=run_local_server, daemon=True)
        server_thread.start()
        time.sleep(2.0)  # даём время подняться
        print(f"Сервер должен быть доступен на http://127.0.0.1:{5000}")
        
    if args.remote_url and args.no_gui:
        print("Указан удалённый URL + --no-gui → ничего не запускаем.")
        sys.exit(0)
        
    # Если --no-gui — просто держим процесс живым (сервер уже работает)
    if args.no_gui:
        print("Режим только сервер (без GUI). Для остановки — Ctrl+C")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("\nОстановка...")
            sys.exit(0)
    else:
        # Запускаем GUI
        url = args.remote_url or f"http://127.0.0.1:{5000}"
        print(f"Открываю десктопное окно по адресу: {url}")
        run_desktop(server_url=url)


if __name__ == "__main__":
    main()