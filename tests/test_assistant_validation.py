from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from backend import main


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DB_PATH', tmp_path / 'test.sqlite')
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'fake-key')
    provider = Mock(side_effect=AssertionError('unexpected provider call'))
    monkeypatch.setattr(main.deepseek, 'call_tool', provider)
    with TestClient(main.app) as client:
        yield client, provider


def payload(**changes):
    tomorrow = (datetime.now(main.LIMA).date() + timedelta(days=1)).isoformat()
    return {'text': 'Necesito una sala para 6 personas', 'date': tomorrow, 'slot_id': 'S15', **changes}


@pytest.mark.parametrize('changes,field,message', [
    ({'date': '20261107'}, 'date', 'YYYY-MM-DD'),
    ({'date': '2099-01-01'}, 'date', 'próximos 7 días'),
    ({'slot_id': 'S99'}, 'slot_id', 'no existe'),
    ({'text': '   '}, 'text', 'solicitud'),
])
def test_invalid_input_stops_provider(isolated, changes, field, message):
    client, provider = isolated
    response = client.post('/api/assistant/propose', json=payload(**changes))
    assert response.status_code == 422
    assert field in response.json()['error']['fields']
    assert message in response.json()['error']['message']
    provider.assert_not_called()


def test_started_slot_stops_provider(isolated, monkeypatch):
    client, provider = isolated
    monkeypatch.setattr(main, 'now_utc', lambda: datetime.now(main.LIMA).replace(hour=15, minute=0, second=0, microsecond=0))
    response = client.post('/api/assistant/propose', json=payload(date=datetime.now(main.LIMA).date().isoformat()))
    assert response.status_code == 422
    assert 'ya comenzó' in response.json()['error']['message']
    provider.assert_not_called()


@pytest.mark.parametrize('text', [
    'Necesito una sala a las 15:00', 'Qué equipamiento tiene R01',
    'Qué equipamiento tiene R02', 'Necesito sala para 6 o 8 personas',
    'Necesito sala para 6 personas y 8 estudiantes', 'Necesito R01 a las 15:00',
    'Qué capacidad tiene R01 para 6 personas?',
    'Necesito una sala para 6 personas sin proyector',
])
def test_clarification_never_calls_provider(isolated, text):
    client, provider = isolated
    response = client.post('/api/assistant/propose', json=payload(text=text))
    assert response.status_code == 200
    assert response.json()['status'] == 'needs_clarification'
    assert response.json()['proposal'] is None
    provider.assert_not_called()


@pytest.mark.parametrize('text,count', [
    ('Necesito una sala para 6 personas', 6),
    ('Para 6 estudiantes a las 15:00', 6),
    ('Necesito una sala para doce personas', 12),
])
def test_explicit_attendees_reach_provider(isolated, text, count):
    client, provider = isolated
    request = payload(text=text)
    provider.side_effect = None
    provider.return_value = {'date': request['date'], 'slot_id': request['slot_id'], 'attendees': count, 'required_equipment': []}
    response = client.post('/api/assistant/propose', json=request)
    assert provider.call_count >= 1
    assert f'asistentes: {count}' in provider.call_args_list[0].args[2]
    if count == 12:
        assert response.json()['status'] == 'no_match'


def test_invented_equipment_is_rejected(isolated):
    client, provider = isolated
    request = payload()
    provider.side_effect = None
    provider.return_value = {'date': request['date'], 'slot_id': request['slot_id'], 'attendees': 6, 'required_equipment': ['projector']}
    response = client.post('/api/assistant/propose', json=request)
    assert response.status_code == 200
    assert response.json()['status'] == 'needs_clarification'
    assert provider.call_count == 1


@pytest.mark.parametrize('text,fragment', [
    ('Necesito espacio para unas 6 u 8 personas', 'cantidad'),
    ('Necesito espacio para 6 o 8 personas', 'cantidad'),
    ('Necesito dos salas para seis estudiantes', 'sola sala'),
    ('6 personas, no hace falta proyector', 'equipos'),
    ('6 personas, sin necesidad de proyector', 'equipos'),
    ('6 personas con proyector, sin pizarra', 'equipos'),
    ('6 personas con o sin proyector', 'equipos'),
    ('Necesito una sala para 12 personas el 12 de noviembre', 'fecha'),
    ('Necesito una sala para 6 personas el lunes', 'fecha'),
    ('Necesito sala para 6 personas a las 15:00 o 16:00', 'hora'),
    ('Necesito una sala para 6 alumnos a las 14:00', 'hora'),
    ('Necesito una sala para 6 alumnos de 15:00 a 17:00', 'hora'),
    ('¿Qué equipamiento tiene R01?', 'informativas'),
])
def test_semantic_conflicts_stop_provider(isolated, text, fragment):
    client, provider = isolated
    result = client.post('/api/assistant/propose', json=payload(text=text))
    assert result.status_code == 200
    assert result.json()['status'] == 'needs_clarification'
    assert fragment in result.json()['message']
    assert result.json()['proposal'] is None
    provider.assert_not_called()


@pytest.mark.parametrize('text,count,required,room', [
    ('Necesito una sala para 6 personas', 6, [], 'R01'),
    ('Necesito una sala para 6 alumnos a las 15:00', 6, [], 'R01'),
    ('Necesito una sala que tenga proyector para 6 personas', 6, ['projector'], 'R01'),
    ('6 personas con proyector y Wi-Fi', 6, ['projector', 'wifi'], 'R01'),
    ('6 personas con projector and whiteboard', 6, ['projector', 'whiteboard'], 'R01'),
    ('Necesito PCs para 4 personas', 4, ['pc'], 'R01'),
    ('Necesito computadores para 4 personas', 4, ['pc'], 'R01'),
    ('Quiero R02 para 4 personas', 4, [], 'R02'),
])
def test_complete_proposal_preserves_constraints(isolated, monkeypatch, text, count, required, room):
    client, provider = isolated
    request = payload(text=text)
    search = {'date': request['date'], 'slot_id': request['slot_id'], 'attendees': count, 'required_equipment': required}
    candidates = [{**search, 'room_id': room}]
    monkeypatch.setattr(main, 'room_candidates', lambda *args: candidates)
    provider.side_effect = lambda name, schema, prompt: search if name == 'search_rooms' else candidates[0]
    result = client.post('/api/assistant/propose', json=request)
    assert result.status_code == 200
    assert result.json()['status'] == 'proposed'
    assert result.json()['proposal'] == candidates[0]
    assert provider.call_count == 2
    with main.closing(main.connect()) as db:
        assert db.execute('SELECT count(*) FROM reservations').fetchone()[0] == 0


def test_specific_room_cannot_be_replaced(isolated, monkeypatch):
    client, provider = isolated
    request = payload(text='Quiero R02 para 4 personas')
    search = {'date': request['date'], 'slot_id': request['slot_id'], 'attendees': 4, 'required_equipment': []}
    provider.side_effect = None
    provider.return_value = search
    monkeypatch.setattr(main, 'room_candidates', lambda *args: [{**search, 'room_id': 'R01'}])
    result = client.post('/api/assistant/propose', json=request)
    assert result.status_code == 200
    assert result.json()['status'] == 'no_match'
    assert 'R02' in result.json()['message']
    assert result.json()['proposal'] is None
    assert provider.call_count == 1


def test_omitted_equipment_cannot_generate_proposal(isolated):
    client, provider = isolated
    request = payload(text='6 personas con proyector y Wi-Fi')
    provider.side_effect = None
    provider.return_value = {'date': request['date'], 'slot_id': request['slot_id'], 'attendees': 6, 'required_equipment': []}
    result = client.post('/api/assistant/propose', json=request)
    assert result.status_code == 200
    assert result.json()['status'] == 'needs_clarification'
    assert result.json()['proposal'] is None
    assert provider.call_count == 1


@pytest.mark.parametrize('text', [
    'No quiero R02 para 4 personas',
    'Necesito una sala para 4 personas, excepto R02',
    'Quiero cualquier sala menos R02 para 4 personas',
    'Evita R02, somos 4 personas',
    'No quiero R02; prefiero R01 para 4 personas',
    'No quiero la sala R02 para 4 personas',
    'R02 no, para 4 personas',
])
def test_excluded_room_clarifies_without_provider_or_reservation(isolated, text):
    client, provider = isolated
    result = client.post('/api/assistant/propose', json=payload(text=text))
    assert result.status_code == 200
    assert result.json()['status'] == 'needs_clarification'
    assert 'no admite excluir salas' in result.json()['message']
    assert result.json()['proposal'] is None
    assert result.json()['tool_trace'] == []
    provider.assert_not_called()
    with main.closing(main.connect()) as db:
        assert db.execute('SELECT count(*) FROM reservations').fetchone()[0] == 0


@pytest.mark.parametrize('text,expected_ids', [
    ('Quiero R02 para 4 personas', {'R02'}),
    ('Necesito una sala para 4 personas', {'R01', 'R02', 'R03'}),
    ('No, quiero R02 para 4 personas', {'R02'}),
    ('No tengo preferencia, quiero R02 para 4 personas', {'R02'}),
])
def test_positive_room_and_conversational_no_keep_candidate_scope(isolated, text, expected_ids):
    import json
    client, provider = isolated
    request = payload(text=text)
    search = {'date': request['date'], 'slot_id': request['slot_id'], 'attendees': 4, 'required_equipment': []}
    def fake_tool(name, schema, prompt):
        if name == 'search_rooms':
            return search
        candidates = json.loads(prompt.split(': ', 1)[1])
        assert {candidate['room_id'] for candidate in candidates} == expected_ids
        return candidates[0]
    provider.side_effect = fake_tool
    result = client.post('/api/assistant/propose', json=request)
    assert result.status_code == 200
    assert result.json()['status'] == 'proposed'
    assert result.json()['proposal']['room_id'] in expected_ids
    assert {key: value for key, value in result.json()['proposal'].items() if key != 'room_id'} == search
    assert provider.call_count == 2
    with main.closing(main.connect()) as db:
        assert db.execute('SELECT count(*) FROM reservations').fetchone()[0] == 0
