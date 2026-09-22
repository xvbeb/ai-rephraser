from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel


@dataclass(frozen=True)
class Message:
    role: Literal["user", "assistant"]
    content: str


class LLMProvider(ABC):
    """System instructions stay separate from role-bearing conversation turns."""

    @abstractmethod
    def generate_json(self, system: str, messages: Sequence[Message],
                      schema: type[BaseModel]) -> str:
        """Return JSON for application validation, or raise AIError."""

    @abstractmethod
    def stream_text(self, system: str, messages: Sequence[Message]) -> Iterator[str]:
        """Yield plain text; raise AIError on failure, including mid-stream."""
