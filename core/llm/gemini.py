from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from json import JSONDecodeError

import httpx
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from core.errors import AIError, InvalidResponse, MissingAPIKey, ProviderTimeout
from .base import LLMProvider, Message


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, timeout_ms: int = 30_000) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_ms = timeout_ms

    @contextmanager
    def _client(self) -> Iterator[genai.Client]:
        if not self.api_key.strip():
            raise MissingAPIKey()
        try:
            with genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(
                    timeout=self.timeout_ms,
                    retry_options=types.HttpRetryOptions(attempts=1),
                ),
            ) as client:
                yield client
        except (httpx.TimeoutException, TimeoutError) as exc:
            raise ProviderTimeout() from exc
        except errors.APIError as exc:
            if exc.code in (408, 504):
                raise ProviderTimeout() from exc
            raise AIError() from exc
        except (JSONDecodeError, ValidationError) as exc:
            raise InvalidResponse() from exc
        except (httpx.HTTPError, ConnectionError) as exc:
            raise AIError() from exc

    @staticmethod
    def _contents(messages: Sequence[Message]) -> list[types.Content]:
        return [types.Content(
            role="model" if message.role == "assistant" else "user",
            parts=[types.Part.from_text(text=message.content)],
        ) for message in messages]

    @staticmethod
    def _check_finish(response: types.GenerateContentResponse) -> None:
        for candidate in response.candidates or []:
            if candidate.finish_reason not in (None, types.FinishReason.STOP):
                raise InvalidResponse()

    def generate_json(self, system: str, messages: Sequence[Message],
                      schema: type[BaseModel]) -> str:
        with self._client() as client:
            response = client.models.generate_content(
                model=self.model, contents=self._contents(messages),
                config=types.GenerateContentConfig(
                    system_instruction=system, response_mime_type="application/json",
                    response_json_schema=schema.model_json_schema(), max_output_tokens=8192,
                ),
            )
            self._check_finish(response)
            if not response.candidates or response.candidates[0].finish_reason != types.FinishReason.STOP:
                raise InvalidResponse()
            if not response.text:
                raise InvalidResponse()
            return response.text

    def stream_text(self, system: str, messages: Sequence[Message]) -> Iterator[str]:
        with self._client() as client:
            stream = client.models.generate_content_stream(
                model=self.model, contents=self._contents(messages),
                config=types.GenerateContentConfig(
                    system_instruction=system, max_output_tokens=8192,
                ),
            )
            finished = False
            try:
                for chunk in stream:
                    self._check_finish(chunk)
                    finished = finished or any(
                        candidate.finish_reason == types.FinishReason.STOP
                        for candidate in chunk.candidates or []
                    )
                    if chunk.text:
                        yield chunk.text
                if not finished:
                    raise InvalidResponse()
            finally:
                stream.close()
