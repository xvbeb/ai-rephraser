from unittest.mock import Mock
import pytest
from google import genai
from core.llm import LLMProvider
from web.app import create_app


@pytest.fixture(autouse=True)
def no_live_gemini(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Tests must never create a live Gemini client")
    monkeypatch.setattr(genai, "Client", forbidden)


@pytest.fixture
def provider():
    fake = Mock(spec=LLMProvider)
    fake.generate_json.return_value = '{"rewritten_text":"Исправлено.","changes":[{"type":"grammar","description":"Исправлена грамматика."}]}'
    fake.stream_text.side_effect = lambda *args: iter(["Короче", "."])
    return fake


@pytest.fixture
def app(provider):
    return create_app({"TESTING": True, "SECRET_KEY": "test-only"}, provider)


@pytest.fixture
def client(app):
    return app.test_client()
