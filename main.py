"""Web/desktop launcher; server-only mode does not import Qt."""
import argparse
import threading

from core.config import BASE_URL, HOST, PORT


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Переписыватель Neon")
    parser.add_argument("--remote-url", help="Подключиться к удалённому серверу")
    parser.add_argument("--no-gui", action="store_true", help="Запустить только сервер")
    args = parser.parse_args()
    if args.remote_url and args.no_gui:
        parser.error("--remote-url нельзя использовать вместе с --no-gui")
    if args.no_gui:
        from web.app import app
        app.run(host=HOST, port=PORT, debug=False, use_reloader=False, threaded=True)
        return
    from desktop.gui import run_desktop, run_local_server
    server = None
    if not args.remote_url:
        # make_server binds synchronously, so Qt cannot race server startup.
        from werkzeug.serving import make_server
        from web.app import app
        server = make_server(HOST, PORT, app, threaded=True)
        threading.Thread(target=run_local_server, args=(server,), daemon=True).start()
    try:
        run_desktop(server_url=args.remote_url or BASE_URL)
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
