import pytest
from core.conversations import ConversationStore
from core.errors import ConversationBusy, StoreFull
from core.llm import Message


def pair(text):
    return [Message('user', text), Message('assistant', text)]


def test_limits_keep_complete_pairs():
    store = ConversationStore(max_messages=4, max_chars=12)
    with store.lease('a') as item:
        store.commit(item, pair('old') + pair('new') + pair('end'))
    assert store.read('a') == pair('new') + pair('end')
    with store.lease('a') as item:
        store.commit(item, pair('longer') + pair('end'))
    assert store.read('a') == pair('end')


def test_ttl_capacity_and_busy_protection():
    store = ConversationStore(max_sessions=1)
    with store.lease('a') as item:
        item.touched -= 4000
        with pytest.raises(ConversationBusy):
            with store.lease('a'):
                pass
        with pytest.raises(StoreFull):
            store.read('b')
    item.touched -= 4000
    assert store.read('b') == []


def test_exception_releases_lease():
    store = ConversationStore()
    with pytest.raises(ValueError):
        with store.lease('a'):
            raise ValueError()
    with store.lease('a') as item:
        assert not item.messages
