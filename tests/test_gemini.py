from unittest.mock import MagicMock
import httpx
import pytest
from google.genai import errors, types
from core.errors import AIError, InvalidResponse, MissingAPIKey, ProviderTimeout
from core.llm import Message
from core.llm.gemini import GeminiProvider
from core.schemas import RephraseResult


@pytest.fixture
def sdk(monkeypatch):
    factory = MagicMock()
    client = factory.return_value.__enter__.return_value
    monkeypatch.setattr('core.llm.gemini.genai.Client', factory)
    return factory, client


def test_sdk_schema_and_roles(sdk):
    factory, client = sdk
    client.models.generate_content.return_value = types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(parts=[types.Part(text='{}')]), finish_reason='STOP')])
    provider = GeminiProvider('fake-key', 'test-model')
    assert provider.generate_json('system', [Message('user', 'source'), Message('assistant', 'draft')], RephraseResult) == '{}'
    args = client.models.generate_content.call_args.kwargs
    assert [m.role for m in args['contents']] == ['user', 'model']
    assert args['config'].system_instruction == 'system'
    assert args['config'].response_json_schema == RephraseResult.model_json_schema()
    assert args['config'].response_mime_type == 'application/json'
    assert factory.call_args.kwargs['http_options'].timeout == 30000
    factory.return_value.__exit__.assert_called_once()


@pytest.mark.parametrize('exception,expected', [
    (httpx.ReadTimeout('secret'), ProviderTimeout),
    (httpx.ConnectError('secret'), AIError),
    (errors.APIError(429, {'error': {'message':'private'}}), AIError),
    (errors.APIError(504, {'error': {'message':'private'}}), ProviderTimeout),
])
def test_sdk_errors(sdk, exception, expected):
    _, client = sdk
    client.models.generate_content.side_effect = exception
    with pytest.raises(expected):
        GeminiProvider('fake', 'model').generate_json('sys', [], RephraseResult)


def test_missing_key():
    with pytest.raises(MissingAPIKey):
        GeminiProvider('', 'model').generate_json('sys', [], RephraseResult)


@pytest.mark.parametrize('reason', ['MAX_TOKENS', 'SAFETY'])
def test_incomplete_output_rejected(sdk, reason):
    _, client = sdk
    client.models.generate_content.return_value = types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(parts=[types.Part(text='{}')]), finish_reason=reason)])
    with pytest.raises(InvalidResponse):
        GeminiProvider('fake', 'model').generate_json('sys', [], RephraseResult)


def test_empty_response(sdk):
    _, client = sdk
    client.models.generate_content.return_value = types.GenerateContentResponse()
    with pytest.raises(InvalidResponse):
        GeminiProvider('fake', 'model').generate_json('sys', [], RephraseResult)


def test_stream_sdk_cleanup_and_error(sdk):
    _, client = sdk
    closed = []
    def chunks():
        try:
            yield types.GenerateContentResponse(candidates=[types.Candidate(
                content=types.Content(parts=[types.Part(text='part')]))])
            raise httpx.ReadTimeout('private')
        finally:
            closed.append(True)
    client.models.generate_content_stream.return_value = chunks()
    stream = GeminiProvider('fake', 'model').stream_text('sys', [Message('user','hello')])
    assert next(stream) == 'part'
    with pytest.raises(ProviderTimeout):
        next(stream)
    assert closed == [True]


@pytest.mark.parametrize('finish', [None, 'STOP'])
def test_stream_requires_completion(sdk, finish):
    _, client = sdk
    def chunks():
        yield types.GenerateContentResponse(candidates=[types.Candidate(
            content=types.Content(parts=[types.Part(text='answer')]), finish_reason=finish)])
    client.models.generate_content_stream.return_value = chunks()
    stream = GeminiProvider('fake', 'model').stream_text('sys', [])
    assert next(stream) == 'answer'
    if finish is None:
        with pytest.raises(InvalidResponse):
            next(stream)
    else:
        assert list(stream) == []
