from web.app import app

if __name__ == '__main__':
    print("Тестовый запуск Flask...")
    app.run(debug=True, host="0.0.0.0", port=5001, use_reloader=False)