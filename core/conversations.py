"""Bounded, process-local history keyed by a signed Flask session identifier.

A lease serializes mutations, including streaming, and prevents eviction while
an operation is in flight. Failed or disconnected generations never commit.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic
from collections.abc import Iterator

from core.errors import ConversationBusy, StoreFull
from core.llm import Message


@dataclass
class Conversation:
    messages: list[Message] = field(default_factory=list)
    touched: float = field(default_factory=monotonic)
    busy: bool = False


class ConversationStore:
    def __init__(self, max_sessions: int = 256, ttl_seconds: int = 3600,
                 max_messages: int = 20, max_chars: int = 60000) -> None:
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds
        self.max_messages = max_messages
        self.max_chars = max_chars
        self._items: dict[str, Conversation] = {}
        self._lock = Lock()

    def _get(self, sid: str) -> Conversation:
        now = monotonic()
        for key, value in list(self._items.items()):
            if not value.busy and now - value.touched > self.ttl_seconds:
                del self._items[key]
        if sid not in self._items:
            if len(self._items) >= self.max_sessions:
                raise StoreFull()
            self._items[sid] = Conversation()
        item = self._items[sid]
        item.touched = now
        return item

    def read(self, sid: str) -> list[Message]:
        with self._lock:
            return list(self._get(sid).messages)

    @contextmanager
    def lease(self, sid: str) -> Iterator[Conversation]:
        with self._lock:
            item = self._get(sid)
            if item.busy:
                raise ConversationBusy()
            item.busy = True
        try:
            yield item
        finally:
            with self._lock:
                item.busy = False
                item.touched = monotonic()

    def commit(self, item: Conversation, messages: list[Message]) -> None:
        # Drop whole oldest user/assistant pairs; never clip a draft mid-text.
        messages = list(messages)
        while len(messages) > self.max_messages or sum(len(m.content) for m in messages) > self.max_chars:
            messages = messages[2:]
        with self._lock:
            item.messages = messages
