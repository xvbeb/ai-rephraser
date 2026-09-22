import secrets
from flask import Flask, Response, jsonify
from werkzeug.exceptions import HTTPException

from core.config import app_settings
from core.conversations import ConversationStore
from core.errors import AIError
from core.llm import LLMProvider
from core.llm.gemini import GeminiProvider
from core.service import RephraseService
from .routes import routes


def create_app(config: dict | None = None, provider: LLMProvider | None = None) -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.update(app_settings())
    if config:
        app.config.update(config)
    if not app.config["SECRET_KEY"]:
        if app.config["APP_ENV"] != "development" and not app.testing:
            raise RuntimeError("SECRET_KEY must be configured outside local development")
        app.config["SECRET_KEY"] = secrets.token_hex(32)
    app.extensions["rephrase_service"] = RephraseService(
        provider if provider is not None else GeminiProvider(
            app.config["GEMINI_API_KEY"], app.config["AI_MODEL"], app.config["AI_TIMEOUT_MS"],
        )
    )
    app.extensions["conversations"] = ConversationStore()
    app.register_blueprint(routes)

    @app.errorhandler(AIError)
    def ai_error(error: AIError) -> tuple[Response, int]:
        return jsonify(error=error.message, code=error.code), error.status

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException) -> tuple[Response, int]:
        messages = {400: "Некорректный JSON.", 413: "Запрос слишком большой.",
                    415: "Ожидается Content-Type: application/json."}
        return jsonify(error=messages.get(error.code, "Запрос не может быть обработан."),
                       code="http_error"), error.code or 500

    @app.errorhandler(Exception)
    def unexpected_error(error: Exception) -> tuple[Response, int]:
        # Log the type only: exception strings may include provider credentials or text.
        app.logger.error("Unhandled application error: %s", type(error).__name__)
        return jsonify(error="Внутренняя ошибка сервера.", code="internal_error"), 500

    return app


app = create_app()
