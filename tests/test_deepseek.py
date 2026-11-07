import json
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from backend import deepseek, main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "db.sqlite")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with TestClient(main.app) as c:
        yield c


def payload():
    day = (datetime.now(ZoneInfo("America/Lima")) + timedelta(days=1)).date().isoformat()
    return {"text": "Una sala para 4 personas con proyector", "date": day, "slot_id": "S14"}


def response(name, arguments):
    call = SimpleNamespace(type="function", function=SimpleNamespace(name=name, arguments=arguments))
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[call]))])


def test_missing_key_and_health(client):
    health = client.get('/api/health').json()
    assert health['status'] == 'ok' and not health['llm_configured']
    assert health['llm_provider'] == 'deepseek' and health['llm_model'] == 'deepseek-flash'
    assert client.post('/api/assistant/propose', json=payload()).status_code == 503


def test_configuration_and_tool_call(monkeypatch):
    import openai
    deepseek._client.cache_clear()
    fake = Mock()
    fake.chat.completions.create.return_value = response('search_rooms', '{"attendees":4}')
    factory = Mock(return_value=fake)
    monkeypatch.setattr(openai, 'OpenAI', factory)
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'fake-key')
    monkeypatch.delenv('DEEPSEEK_MODEL', raising=False)
    assert deepseek.call_tool('search_rooms', {}, 'busca para 4') == {'attendees': 4}
    assert factory.call_args.kwargs['base_url'] == 'https://api.deepseek.com'
    kwargs = fake.chat.completions.create.call_args.kwargs
    assert kwargs['model'] == 'deepseek-flash'
    assert kwargs['tool_choice']['function']['name'] == 'search_rooms'
    deepseek._client.cache_clear()


@pytest.mark.parametrize('name,args', [('other', '{}'), ('search_rooms', '{bad'),
    ('search_rooms', '{"x":1,"x":2}')])
def test_rejects_invalid_calls(monkeypatch, name, args):
    fake = Mock()
    fake.chat.completions.create.return_value = response(name, args)
    monkeypatch.setattr(deepseek, '_client', lambda key: fake)
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'fake-key')
    with pytest.raises(deepseek.ProviderError):
        deepseek.call_tool('search_rooms', {}, 'test')


@pytest.mark.parametrize('error', [RuntimeError('401'), RuntimeError('429'), TimeoutError(), RuntimeError('provider')])
def test_provider_errors_are_sanitized(monkeypatch, error):
    fake = Mock()
    fake.chat.completions.create.side_effect = error
    monkeypatch.setattr(deepseek, '_client', lambda key: fake)
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'fake-key')
    with pytest.raises(deepseek.ProviderError, match='provider_unavailable'):
        deepseek.call_tool('search_rooms', {}, 'test')


def test_proposal_is_validated_and_does_not_reserve(client, monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'fake-key')
    p = payload()
    search = {'date': p['date'], 'slot_id': p['slot_id'], 'attendees': 4, 'required_equipment': ['projector']}
    def fake_tool(name, schema, prompt):
        return search if name == 'search_rooms' else {**search, 'room_id': 'R01'}
    monkeypatch.setattr(deepseek, 'call_tool', fake_tool)
    result = client.post('/api/assistant/propose', json=p)
    assert result.status_code == 200 and result.json()['status'] == 'proposed'
    assert result.json()['tool_trace'] == ['search_rooms', 'propose_reservation']
    assert client.get('/api/rooms', params={'date': p['date'], 'slot_id': p['slot_id']}).json()['rooms'][0]['reservation_state'] == 'available'


def test_incompatible_proposal_is_rejected(client, monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'fake-key')
    p = payload()
    search = {'date': p['date'], 'slot_id': p['slot_id'], 'attendees': 4, 'required_equipment': ['projector']}
    monkeypatch.setattr(deepseek, 'call_tool', lambda name, schema, prompt: search if name == 'search_rooms' else {**search, 'room_id': 'R02'})
    assert client.post('/api/assistant/propose', json=p).status_code == 503
