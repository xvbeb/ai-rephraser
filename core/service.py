from collections.abc import Iterator, Sequence
from pydantic import ValidationError

from core.errors import InvalidRequest, InvalidResponse
from core.llm import LLMProvider, Message
from core.prompts import build_chat_prompt, build_rephrase_prompt
from core.prompts.rephrase import tone_instruction
from core.schemas import RephraseResult

MAX_INPUT_CHARS = 12000
MAX_OUTPUT_CHARS = 24000


def validate_input(data: object, field: str) -> tuple[str, str]:
    if not isinstance(data, dict):
        raise InvalidRequest()
    text, tone = data.get(field), data.get("tone", "neutral")
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_INPUT_CHARS:
        raise InvalidRequest()
    if not isinstance(tone, str):
        raise InvalidRequest()
    tone_instruction(tone)
    return text.strip(), tone


class RephraseService:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def rephrase(self, text: str, tone: str) -> RephraseResult:
        raw = self.provider.generate_json(
            build_rephrase_prompt(tone), [Message("user", text)], RephraseResult,
        )
        try:
            return RephraseResult.model_validate_json(raw)
        except ValidationError as exc:
            raise InvalidResponse() from exc

    def refine(self, history: Sequence[Message], text: str, tone: str) -> Iterator[str]:
        size = 0
        has_text = False
        stream = self.provider.stream_text(
            build_chat_prompt(tone), [*history, Message("user", text)],
        )
        try:
            for chunk in stream:
                if not isinstance(chunk, str):
                    raise InvalidResponse()
                size += len(chunk)
                if size > MAX_OUTPUT_CHARS:
                    raise InvalidResponse()
                has_text = has_text or bool(chunk.strip())
                if chunk:
                    yield chunk
            if not has_text:
                raise InvalidResponse()
        finally:
            close = getattr(stream, "close", None)
            if close is not None:
                close()
