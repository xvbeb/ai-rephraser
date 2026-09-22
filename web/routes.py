import json
import secrets
from dataclasses import asdict
from collections.abc import Iterator

from flask import Blueprint, Response, current_app, jsonify, render_template, request, session

from core.conversations import ConversationStore
from core.errors import AIError
from core.llm import Message
from core.prompts import TONES
from core.service import RephraseService, validate_input

routes = Blueprint("main", __name__)


def dependencies() -> tuple[RephraseService, ConversationStore, str]:
    if "conversation_id" not in session:
        session["conversation_id"] = secrets.token_urlsafe(32)
    return (current_app.extensions["rephrase_service"],
            current_app.extensions["conversations"], session["conversation_id"])


def serialize(messages: list[Message]) -> list[dict]:
    return [asdict(message) for message in messages]


@routes.get("/")
def index() -> str:
    return render_template("index.html")


@routes.post("/rephrase")
def rephrase() -> Response:
    text, tone = validate_input(request.get_json(), "text")
    service, store, sid = dependencies()
    with store.lease(sid) as conversation:
        result = service.rephrase(text, tone)
        # A new source text starts a new refinement conversation.
        store.commit(conversation, [Message("user", text), Message("assistant", result.rewritten_text)])
    return jsonify(result.model_dump())


@routes.route("/chat", methods=["GET", "POST"])
def chat() -> Response:
    if request.method == "GET":
        _, store, sid = dependencies()
        return jsonify(history=serialize(store.read(sid)))
    text, tone = validate_input(request.get_json(), "message")
    service, store, sid = dependencies()
    with store.lease(sid) as conversation:
        answer = "".join(service.refine(conversation.messages, text, tone))
        store.commit(conversation, [*conversation.messages, Message("user", text), Message("assistant", answer)])
        return jsonify(history=serialize(conversation.messages))


def event(kind: str, **data: object) -> str:
    return f"event: {kind}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@routes.post("/chat/stream")
def chat_stream() -> Response:
    text, tone = validate_input(request.get_json(), "message")
    service, store, sid = dependencies()
    lease = store.lease(sid)
    conversation = lease.__enter__()
    stream = service.refine(conversation.messages, text, tone)
    # Prime the stream before headers are sent so initial failures use HTTP errors.
    try:
        first = next(stream)
    except BaseException:
        lease.__exit__(None, None, None)
        stream.close()
        raise

    logger = current_app.logger
    closed = False

    def cleanup() -> None:
        nonlocal closed
        if not closed:
            closed = True
            try:
                stream.close()
            finally:
                lease.__exit__(None, None, None)

    def generate() -> Iterator[str]:
        chunks = [first]
        try:
            yield event("delta", text=first)
            for chunk in stream:
                chunks.append(chunk)
                yield event("delta", text=chunk)
            answer = "".join(chunks)
            store.commit(conversation, [*conversation.messages, Message("user", text), Message("assistant", answer)])
            yield event("done", history=serialize(conversation.messages))
        except AIError as error:
            yield event("error", error=error.message, code=error.code)
        except Exception as error:
            logger.error("Unhandled stream error: %s", type(error).__name__)
            yield event("error", error="Ошибка при получении ответа.", code="internal_error")
        finally:
            cleanup()

    response = Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache, no-store", "X-Accel-Buffering": "no",
    })
    response.call_on_close(cleanup)
    return response


@routes.post("/chat/clear")
def clear_chat() -> Response:
    _, store, sid = dependencies()
    with store.lease(sid) as conversation:
        store.commit(conversation, [])
    return jsonify(status="cleared")


@routes.get("/tones")
def get_tones() -> Response:
    return jsonify(tones=list(TONES))
