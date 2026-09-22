"""Optional local development entry point on port 5001."""
from core.config import DEBUG, HOST
from web.app import app

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=5001, use_reloader=False)
