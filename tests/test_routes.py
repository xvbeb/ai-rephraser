import json
import pytest
from core.errors import AIError, InvalidResponse, MissingAPIKey, ProviderTimeout
from web.app import create_app


@pytest.mark.parametrize("data", [None, [], "text", {}, {"text": " "}, {"text": 1},
    {"text": "x" * 12001}, {"text": "x", "tone": []}])
def test_rephrase_validation(client, provider, data):
    response = client.post('/rephrase', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 400
    provider.generate_json.assert_not_called()


def test_tones(client):
    assert {"neutral", "formal", "professional", "creative"} <= set(client.get('/tones').json['tones'])
    response = client.post('/rephrase', json={"text": "x", "tone": "unknown"})
    assert response.status_code == 400
    assert response.json['code'] == 'unsupported_tone'


def test_http_errors(client):
    assert client.post('/rephrase', data='bad', content_type='application/json').status_code == 400
    assert client.post('/rephrase', data='bad').status_code == 415
    assert client.post('/rephrase', json={"text": "x" * 100001}).status_code == 413


@pytest.mark.parametrize("error,status", [(AIError(),502), (InvalidResponse(),502),
                                        (MissingAPIKey(),503), (ProviderTimeout(),504)])
def test_error_status_and_history(client, provider, error, status):
    provider.generate_json.side_effect = error
    response = client.post('/rephrase', json={"text": "source"})
    assert response.status_code == status
    assert response.json['code'] == error.code
    assert client.get('/chat').json['history'] == []


def test_malformed_response_route(client, provider):
    provider.generate_json.return_value = 'raw secret output'
    response = client.post('/rephrase', json={"text": "source"})
    assert response.status_code == 502
    assert b'raw secret' not in response.data


def test_history_reset_clear_and_isolation(client, app):
    result = client.post('/rephrase', json={"text": "source"})
    assert set(result.json) == {'rewritten_text', 'changes'}
    assert len(client.post('/chat', json={"message": "shorter"}).json['history']) == 4
    assert app.test_client().get('/chat').json['history'] == []
    client.post('/rephrase', json={"text": "new source"})
    assert len(client.get('/chat').json['history']) == 2
    client.post('/chat/clear')
    assert client.get('/chat').json['history'] == []


def test_stream_progress_and_commit(client):
    response = client.post('/chat/stream', json={"message": "shorter"}, buffered=False)
    assert response.mimetype == 'text/event-stream'
    assert b'event: delta' in next(response.response)
    assert client.get('/chat').json['history'] == []
    assert client.post('/chat/clear').status_code == 409
    body = b''.join(response.response).decode()
    assert 'event: done' in body
    assert client.get('/chat').json['history'][-1]['content'] == 'Короче.'
    response.close()
    assert client.post('/chat/clear').status_code == 200


def test_stream_initial_failure(client, provider):
    provider.stream_text.side_effect = ProviderTimeout()
    response = client.post('/chat/stream', json={"message": "shorter"})
    assert response.status_code == 504
    assert client.post('/chat/clear').status_code == 200


def test_stream_late_failure(client, provider):
    def fail(*args):
        yield 'partial'
        raise AIError('secret provider details')
    provider.stream_text.side_effect = fail
    response = client.post('/chat/stream', json={"message": "shorter"})
    body = response.data.decode()
    assert 'event: error' in body and 'event: done' not in body
    assert 'secret provider details' not in body
    assert client.get('/chat').json['history'] == []
    assert client.post('/chat/clear').status_code == 200


def test_disconnect_releases_lease(client):
    response = client.post('/chat/stream', json={"message": "shorter"}, buffered=False)
    next(response.response)
    response.close()
    assert client.get('/chat').json['history'] == []
    assert client.post('/chat/clear').status_code == 200


def test_session_cookie_contains_no_draft(client):
    response = client.post('/rephrase', json={"text": "sensitive text"})
    assert len(response.headers.get('Set-Cookie', '')) < 512
    with client.session_transaction() as session:
        assert set(session) == {'conversation_id'}


def test_production_requires_secret():
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        create_app({"APP_ENV": "production", "SECRET_KEY": None})


def test_random_development_secrets():
    config = {"APP_ENV": "development", "SECRET_KEY": None}
    assert create_app(config).secret_key != create_app(config).secret_key


def test_unexpected_error_sanitized(client, provider):
    provider.generate_json.side_effect = RuntimeError('private detail')
    response = client.post('/rephrase', json={"text": "source"})
    assert response.status_code == 500
    assert b'private detail' not in response.data
