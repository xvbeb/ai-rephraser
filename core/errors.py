"""Safe application errors; provider details never cross the API boundary."""


class AIError(Exception):
    status = 502
    code = "provider_failure"
    message = "Сервис ИИ временно недоступен. Попробуйте ещё раз."


class MissingAPIKey(AIError):
    status = 503
    code = "missing_api_key"
    message = "Сервис ИИ не настроен: требуется GEMINI_API_KEY."


class ProviderTimeout(AIError):
    status = 504
    code = "provider_timeout"
    message = "Сервис ИИ не успел ответить. Попробуйте ещё раз."


class InvalidResponse(AIError):
    code = "invalid_ai_response"
    message = "ИИ вернул некорректный или неполный ответ. Попробуйте ещё раз."


class InvalidRequest(AIError):
    status = 400
    code = "invalid_request"
    message = "Передайте непустой текст (до 12000 символов) и допустимый тон."


class UnsupportedTone(InvalidRequest):
    code = "unsupported_tone"
    message = "Выбран неподдерживаемый тон."


class ConversationBusy(AIError):
    status = 409
    code = "conversation_busy"
    message = "Дождитесь завершения текущего запроса."


class StoreFull(AIError):
    status = 503
    code = "server_busy"
    message = "Сервер занят. Попробуйте позже."
