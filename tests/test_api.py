from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from backend import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setenv("VISION_INGEST_TOKEN", "test-ingest-token")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with TestClient(main.app) as test_client:
        yield test_client


def future_slot():
    local = datetime.now(ZoneInfo("America/Lima"))
    slots = [("S09", time(9)), ("S10", time(10)), ("S11", time(11)),
             ("S14", time(14)), ("S15", time(15)), ("S16", time(16)),
             ("S17", time(17)), ("S18", time(18))]
    for slot_id, starts in slots:
        if local.time().replace(tzinfo=None) < starts:
            return local.date().isoformat(), slot_id
    return (local.date() + timedelta(days=1)).isoformat(), "S09"


def reservation_payload(**changes):
    day, slot_id = future_slot()
    payload = {"request_id": str(uuid.uuid4()), "room_id": "R01", "date": day,
               "slot_id": slot_id, "attendees": 4,
               "required_equipment": ["pc", "projector"], "confirmed": True}
    payload.update(changes)
    return payload


def test_catalog_is_synthetic_and_separates_occupancy(client):
    day, slot_id = future_slot()
    response = client.get("/api/rooms", params={"date": day, "slot_id": slot_id})
    assert response.status_code == 200
    rooms = response.json()["rooms"]
    assert [room["room_id"] for room in rooms] == ["R01", "R02", "R03"]
    assert rooms[0]["occupancy"]["state"] == "unknown"
    assert rooms[0]["occupancy"]["count"] is None
    assert rooms[1]["occupancy"]["reason"] == "no_sensor"


def test_reservation_persists_and_same_request_id_replays(client):
    payload = reservation_payload()
    created = client.post("/api/reservations", json=payload)
    replay = client.post("/api/reservations", json=payload)
    assert created.status_code == 201
    assert replay.status_code == 200
    assert replay.json()["reservation_id"] == created.json()["reservation_id"]
    assert client.get("/api/rooms", params={"date": payload["date"], "slot_id": payload["slot_id"]})\
        .json()["rooms"][0]["reservation_state"] == "reserved"


def test_different_request_id_cannot_double_book_same_slot(client):
    first = reservation_payload()
    second = {**first, "request_id": str(uuid.uuid4())}
    assert client.post("/api/reservations", json=first).status_code == 201
    conflict = client.post("/api/reservations", json=second)
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "reservation_conflict"


@pytest.mark.parametrize("changes,code", [
    ({"attendees": 7}, "capacity_exceeded"),
    ({"required_equipment": ["whiteboard"]}, "equipment_unavailable"),
    ({"confirmed": False}, "confirmation_required"),
])
def test_reservation_rules_are_checked_by_backend(client, changes, code):
    response = client.post("/api/reservations", json=reservation_payload(**changes))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == code


def test_telemetry_requires_token_and_zero_means_no_detections(client):
    day, slot_id = future_slot()
    payload = {"source_id": "vision-david", "room_id": "R01", "mode": "live_camera",
               "status": "ok", "count": 0,
               "observed_at": datetime.now(timezone.utc).isoformat()}
    denied = client.post("/api/telemetry", json=payload)
    accepted = client.post("/api/telemetry", json=payload,
                           headers={"Authorization": "Bearer test-ingest-token"})
    occupancy = client.get("/api/rooms", params={"date": day, "slot_id": slot_id}).json()["rooms"][0]["occupancy"]
    assert denied.status_code == 401
    assert accepted.status_code == 202
    assert occupancy["state"] == "no_detections"
    assert occupancy["count"] == 0


def test_telemetry_rejects_boolean_count(client):
    payload = {"source_id": "vision-david", "room_id": "R01", "mode": "live_camera",
               "status": "ok", "count": True,
               "observed_at": datetime.now(timezone.utc).isoformat()}
    response = client.post("/api/telemetry", json=payload,
                           headers={"Authorization": "Bearer test-ingest-token"})
    assert response.status_code == 422
