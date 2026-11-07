from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from contextlib import closing
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("CAMPUSTWIN_DB", str(ROOT / "backend" / "campustwin.db")))
if not DB_PATH.is_absolute():
    DB_PATH = ROOT / DB_PATH
LIMA = ZoneInfo("America/Lima")
UTC = timezone.utc
from backend import deepseek
SLOTS: dict[str, tuple[time, time]] = {
    "S09": (time(9), time(10)), "S10": (time(10), time(11)),
    "S11": (time(11), time(12)), "S14": (time(14), time(15)),
    "S15": (time(15), time(16)), "S16": (time(16), time(17)),
    "S17": (time(17), time(18)), "S18": (time(18), time(19)),
}
ROOM_SEED = (
    ("R01", "Sala multimedia", 6, ("pc", "projector", "wifi")),
    ("R02", "Sala de estudio", 8, ("whiteboard", "wifi")),
    ("R03", "Cubículo de investigación", 4, ("wifi",)),
)
ROOM_IDS = {row[0] for row in ROOM_SEED}
EQUIPMENT = {item for _, _, _, items in ROOM_SEED for item in items}


def now_utc() -> datetime:
    return datetime.now(UTC)


def error_body(code: str, message: str, fields: list[str] | None = None) -> dict:
    return {"error": {"code": code, "message": message, "fields": fields or []}}


class APIError(Exception):
    def __init__(self, status: int, code: str, message: str, fields: list[str] | None = None):
        self.status, self.code, self.message, self.fields = status, code, message, fields or []


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReservationIn(StrictModel):
    request_id: str
    room_id: str
    date: str
    slot_id: str
    attendees: int = Field(strict=True, ge=1, le=100)
    required_equipment: list[str]
    confirmed: bool = Field(strict=True)

    @field_validator("request_id")
    @classmethod
    def valid_request_id(cls, value: str) -> str:
        try:
            return str(uuid.UUID(value))
        except ValueError as exc:
            raise ValueError("request_id debe ser UUID") from exc

    @field_validator("room_id")
    @classmethod
    def valid_room_id(cls, value: str) -> str:
        if value not in ROOM_IDS:
            raise ValueError("room_id desconocido")
        return value

    @field_validator("slot_id")
    @classmethod
    def valid_slot_id(cls, value: str) -> str:
        if value not in SLOTS:
            raise ValueError("slot_id desconocido")
        return value

    @field_validator("date")
    @classmethod
    def valid_date_syntax(cls, value: str) -> str:
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise ValueError("date debe usar YYYY-MM-DD") from exc

    @field_validator("required_equipment")
    @classmethod
    def valid_equipment(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)) or any(item not in EQUIPMENT for item in value):
            raise ValueError("equipamiento desconocido o repetido")
        return sorted(value)


class AssistantIn(StrictModel):
    text: str = Field(min_length=1, max_length=500)
    date: str
    slot_id: str

    @field_validator("text")
    @classmethod
    def nonblank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("text no puede estar vacío")
        return value

    @field_validator("date")
    @classmethod
    def valid_date_syntax(cls, value: str) -> str:
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError("formato inválido")
            return date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise ValueError("date debe usar YYYY-MM-DD") from exc

    @field_validator("slot_id")
    @classmethod
    def valid_slot_id(cls, value: str) -> str:
        if value not in SLOTS:
            raise ValueError("slot_id desconocido")
        return value


class TelemetryIn(StrictModel):
    source_id: Literal["vision-david"]
    room_id: Literal["R01"]
    mode: Literal["live_camera", "authorized_clip"]
    status: Literal["ok", "error"]
    count: int | None = Field(strict=True)
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at debe incluir zona horaria")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_count(self):
        if self.status == "ok":
            if type(self.count) is not int or not 0 <= self.count <= 100:
                raise ValueError("count debe ser entero de 0 a 100")
        elif self.count is not None:
            raise ValueError("count debe ser null para status=error")
        return self


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=2.0, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=2000")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    return db


def initialize_db() -> None:
    with closing(connect()) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS rooms (
            room_id TEXT PRIMARY KEY, name TEXT NOT NULL, capacity INTEGER NOT NULL CHECK(capacity > 0),
            equipment_json TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, disabled_reason TEXT)""")
        db.execute("""CREATE TABLE IF NOT EXISTS reservations (
            reservation_id TEXT PRIMARY KEY, request_id TEXT NOT NULL UNIQUE, payload_json TEXT NOT NULL,
            user_id TEXT NOT NULL DEFAULT 'demo-student', room_id TEXT NOT NULL REFERENCES rooms(room_id),
            date TEXT NOT NULL, slot_id TEXT NOT NULL, attendees INTEGER NOT NULL,
            required_equipment_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'confirmed',
            created_at TEXT NOT NULL, UNIQUE(room_id,date,slot_id))""")
        db.execute("BEGIN IMMEDIATE")
        try:
            for room_id, name, capacity, equipment in ROOM_SEED:
                db.execute("INSERT OR IGNORE INTO rooms(room_id,name,capacity,equipment_json) VALUES(?,?,?,?)",
                    (room_id, name, capacity, json.dumps(equipment)))
            db.execute("COMMIT")
        except Exception:
            db.execute("ROLLBACK")
            raise


def date_allowed(day: date) -> bool:
    today = datetime.now(LIMA).date()
    return today <= day <= today + timedelta(days=7)


def slot_not_started(day: date, slot_id: str, current: datetime | None = None) -> bool:
    local_now = (current or now_utc()).astimezone(LIMA)
    return local_now < datetime.combine(day, SLOTS[slot_id][0], LIMA)


def last_sample() -> dict | None:
    return getattr(app.state, "last_telemetry", None)


def occupancy(room_id: str, current: datetime) -> dict:
    fields = ("source_id", "mode", "observed_at", "received_at", "expires_at")
    if room_id != "R01":
        return {"state": "unknown", "reason": "no_sensor", "count": None, **{f: None for f in fields}}
    sample = last_sample()
    if sample is None:
        return {"state": "unknown", "reason": "no_data", "count": None, **{f: None for f in fields}}
    if sample["mode"] == "authorized_clip":
        return {"state": "unknown", "reason": "recorded_sample", "count": None,
            **{f: None for f in fields}}
    if sample["status"] == "error":
        state, reason, count = "unknown", "camera_error", None
    elif current >= sample["expires_at"]:
        state, reason, count = "unknown", "stale", None
    else:
        state = "people_detected" if sample["count"] > 0 else "no_detections"
        reason, count = None, sample["count"]
    result = {"state": state, "reason": reason, "count": count}
    for field in fields:
        value = sample[field]
        result[field] = value.isoformat().replace("+00:00", "Z") if isinstance(value, datetime) else value
    return result


def room_candidates(date_text: str, slot_id: str, attendees: int, required: list[str]) -> list[dict]:
    day = date.fromisoformat(date_text)
    if not date_allowed(day) or slot_id not in SLOTS or not slot_not_started(day, slot_id):
        return []
    with closing(connect()) as db:
        rows = db.execute("""SELECT r.*, b.reservation_id FROM rooms r LEFT JOIN reservations b
            ON b.room_id=r.room_id AND b.date=? AND b.slot_id=? ORDER BY r.room_id""",
            (date_text, slot_id)).fetchall()
    wanted = set(required)
    return [{"room_id": row["room_id"], "date": date_text, "slot_id": slot_id,
        "attendees": attendees, "required_equipment": sorted(wanted)}
        for row in rows if row["enabled"] and row["reservation_id"] is None
        and row["capacity"] >= attendees and wanted.issubset(json.loads(row["equipment_json"]))]


app = FastAPI(title="CampusTwin AI", version="1.0")


@app.on_event("startup")
def startup() -> None:
    app.state.last_telemetry = None
    initialize_db()


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    body = await request.body()
    if len(body) > 8 * 1024:
        return JSONResponse(status_code=413, content=error_body("body_too_large", "El cuerpo supera 8 KiB."))
    return await call_next(request)


@app.exception_handler(APIError)
async def api_error_handler(_: Request, exc: APIError):
    return JSONResponse(status_code=exc.status, content=error_body(exc.code, exc.message, exc.fields))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    fields = sorted({".".join(str(p) for p in item["loc"] if p != "body") for item in exc.errors()})
    message = "La solicitud no cumple el contrato."
    if request.url.path == "/api/assistant/propose":
        if "date" in fields:
            message = "La fecha debe ser válida y usar YYYY-MM-DD."
        elif "slot_id" in fields:
            message = "La franja indicada no existe."
        elif "text" in fields:
            message = "Escribe una solicitud de entre 1 y 500 caracteres."
    return JSONResponse(status_code=422, content=error_body("invalid_request", message, fields))


@app.get("/api/health")
def health():
    try:
        with closing(connect()) as db:
            db.execute("SELECT 1").fetchone()
    except sqlite3.Error as exc:
        raise APIError(503, "database_unavailable", "La base no está disponible.") from exc
    return {"status": "ok", "api_version": "1.0", "server_time": now_utc().isoformat().replace("+00:00", "Z"),
        "timezone": "America/Lima", "llm_configured": bool(os.getenv("DEEPSEEK_API_KEY")),
        "llm_provider": "deepseek", "llm_model": os.getenv("DEEPSEEK_MODEL", deepseek.DEFAULT_MODEL)}


@app.get("/api/rooms")
def get_rooms(date_text: str = Query(alias="date"), slot_id: str = Query()):
    try:
        day = date.fromisoformat(date_text)
    except ValueError as exc:
        raise APIError(422, "invalid_date", "date debe usar YYYY-MM-DD.", ["date"]) from exc
    if slot_id not in SLOTS:
        raise APIError(422, "invalid_slot", "La franja no existe.", ["slot_id"])
    if not date_allowed(day):
        raise APIError(422, "invalid_date", "La fecha debe estar entre hoy y los próximos 7 días.", ["date"])
    current = now_utc()
    try:
        with closing(connect()) as db:
            rows = db.execute("""SELECT r.*, b.reservation_id FROM rooms r LEFT JOIN reservations b
                ON b.room_id=r.room_id AND b.date=? AND b.slot_id=? ORDER BY r.room_id""",
                (day.isoformat(), slot_id)).fetchall()
    except sqlite3.Error as exc:
        raise APIError(503, "database_unavailable", "No se pudo consultar el catálogo.") from exc
    start, end = SLOTS[slot_id]
    can_book_time = slot_not_started(day, slot_id, current)
    result = []
    for row in rows:
        reserved = row["reservation_id"] is not None
        sample = last_sample() if row["room_id"] == "R01" else None
        recorded_sample = None
        if sample and sample["mode"] == "authorized_clip":
            recorded_sample = {"mode": "authorized_clip", "status": sample["status"],
                "detected_count": sample["count"],
                "observed_at": sample["observed_at"].isoformat().replace("+00:00", "Z")}
        result.append({"room_id": row["room_id"], "name": row["name"], "capacity": row["capacity"],
            "equipment": json.loads(row["equipment_json"]), "enabled": bool(row["enabled"]),
            "disabled_reason": row["disabled_reason"],
            "reservation_state": "reserved" if reserved else "available",
            "reservation_id": row["reservation_id"],
            "bookable": bool(row["enabled"]) and not reserved and can_book_time,
            "occupancy": occupancy(row["room_id"], current), "recorded_sample": recorded_sample})
    return {"api_version": "1.0", "server_time": current.isoformat().replace("+00:00", "Z"),
        "timezone": "America/Lima", "date": day.isoformat(), "slot_id": slot_id,
        "slots": [{"slot_id": key, "start_local": a.strftime("%H:%M"), "end_local": b.strftime("%H:%M")}
            for key, (a, b) in SLOTS.items()], "rooms": result}


def reservation_dict(row: sqlite3.Row) -> dict:
    return {"reservation_id": row["reservation_id"], "request_id": row["request_id"],
        "user_id": "demo-student", "room_id": row["room_id"], "date": row["date"],
        "slot_id": row["slot_id"], "attendees": row["attendees"],
        "required_equipment": json.loads(row["required_equipment_json"]),
        "status": "confirmed", "created_at": row["created_at"]}


@app.post("/api/reservations")
def create_reservation(payload: ReservationIn):
    normalized = {"room_id": payload.room_id, "date": payload.date, "slot_id": payload.slot_id,
        "attendees": payload.attendees, "required_equipment": payload.required_equipment,
        "confirmed": payload.confirmed}
    payload_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    try:
        with closing(connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute("SELECT * FROM reservations WHERE request_id=?", (payload.request_id,)).fetchone()
            if prior is not None:
                if prior["payload_json"] != payload_json:
                    db.execute("ROLLBACK")
                    raise APIError(409, "request_id_conflict", "request_id ya se usó con otros datos.", ["request_id"])
                db.execute("COMMIT")
                return JSONResponse(status_code=200, content=reservation_dict(prior))
            if not payload.confirmed:
                db.execute("ROLLBACK")
                raise APIError(422, "confirmation_required", "Confirma antes de reservar.", ["confirmed"])
            day = date.fromisoformat(payload.date)
            if not date_allowed(day):
                db.execute("ROLLBACK")
                raise APIError(422, "invalid_date", "La fecha debe estar entre hoy y los próximos 7 días.", ["date"])
            if not slot_not_started(day, payload.slot_id):
                db.execute("ROLLBACK")
                raise APIError(422, "invalid_slot", "La franja ya comenzó.", ["slot_id"])
            room = db.execute("SELECT * FROM rooms WHERE room_id=?", (payload.room_id,)).fetchone()
            if room is None:
                db.execute("ROLLBACK")
                raise APIError(404, "room_not_found", "El ambiente no existe.", ["room_id"])
            if not room["enabled"]:
                db.execute("ROLLBACK")
                raise APIError(422, "room_disabled", "El ambiente no está habilitado.", ["room_id"])
            if payload.attendees > room["capacity"]:
                db.execute("ROLLBACK")
                raise APIError(422, "capacity_exceeded", "El aforo solicitado supera la capacidad.", ["attendees"])
            if not set(payload.required_equipment).issubset(json.loads(room["equipment_json"])):
                db.execute("ROLLBACK")
                raise APIError(422, "equipment_unavailable", "El equipo solicitado no está disponible.", ["required_equipment"])
            reservation_id = str(uuid.uuid4())
            created_at = now_utc().isoformat().replace("+00:00", "Z")
            db.execute("""INSERT INTO reservations(reservation_id,request_id,payload_json,
                room_id,date,slot_id,attendees,required_equipment_json,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (reservation_id, payload.request_id, payload_json, payload.room_id, payload.date,
                 payload.slot_id, payload.attendees, json.dumps(payload.required_equipment), created_at))
            created = db.execute("SELECT * FROM reservations WHERE reservation_id=?", (reservation_id,)).fetchone()
            db.execute("COMMIT")
            return JSONResponse(status_code=201, content=reservation_dict(created))
    except APIError:
        raise
    except sqlite3.IntegrityError as exc:
        if "UNIQUE constraint failed: reservations.room_id" in str(exc):
            raise APIError(409, "reservation_conflict", "El ambiente ya tiene reserva en esa franja.",
                           ["room_id", "date", "slot_id"]) from exc
        raise APIError(409, "request_id_conflict", "La solicitud ya existe.", ["request_id"]) from exc
    except sqlite3.OperationalError as exc:
        if "locked" in str(exc).lower() or "busy" in str(exc).lower():
            response = JSONResponse(status_code=503,
                content=error_body("database_busy", "Base ocupada; reintenta con el mismo request_id."))
            response.headers["Retry-After"] = "1"
            return response
        raise APIError(503, "database_unavailable", "No se pudo guardar la reserva.") from exc


class SearchArgs(StrictModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    date: str
    slot_id: str
    attendees: int = Field(ge=1, le=100)
    required_equipment: list[str]


class ProposalArgs(SearchArgs):
    room_id: str


SEARCH_SCHEMA = {"type": "object", "additionalProperties": False,
    "properties": {"date": {"type": "string"}, "slot_id": {"type": "string"},
        "attendees": {"type": "integer"}, "required_equipment": {
            "type": "array", "items": {"type": "string", "enum": sorted(EQUIPMENT)}}},
    "required": ["date", "slot_id", "attendees", "required_equipment"]}
PROPOSAL_SCHEMA = {**SEARCH_SCHEMA,
    "properties": {**SEARCH_SCHEMA["properties"], "room_id": {"type": "string", "enum": sorted(ROOM_IDS)}},
    "required": [*SEARCH_SCHEMA["required"], "room_id"]}


# Only explicit counts tied to people are accepted; unrelated numbers cannot imply attendance.
COUNT_WORDS = {"un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
    "dieciséis": 16, "dieciseis": 16, "veinte": 20}
COUNT_PATTERN = r"(?:\d+|" + "|".join(COUNT_WORDS) + r")"
PEOPLE_PATTERN = r"(?:personas?|estudiantes?|asistentes?|participantes?|alumnos?)"


def assistant_attendees(text: str) -> int | None:
    matches = list(re.finditer(rf"(?<![\w:])({COUNT_PATTERN})\s+{PEOPLE_PATTERN}\b", text, re.IGNORECASE))
    # More than one count, including a range such as '6 o 8 personas', is ambiguous.
    if len(matches) != 1:
        return None
    token = matches[0].group(1).lower()
    prefix = text[:matches[0].start()]
    suffix = text[matches[0].end():]
    if (re.search(r"(?:[\d.,+\-]|\b(?:y|aproximadamente|unos|unas|entre|más de|menos de))\s*$", prefix, re.IGNORECASE)
            or re.search(rf"(?<![\w:]){COUNT_PATTERN}\s*(?:o|u|a|[-–])\s*$", prefix, re.IGNORECASE)
            or re.match(rf"\s*(?:o|u|a|[-–])\s*{COUNT_PATTERN}\b", suffix, re.IGNORECASE)):
        return None
    count = int(token) if token.isdigit() else COUNT_WORDS[token]
    return count if 1 <= count <= 100 else None


EQUIPMENT_ALIASES = {
    "pc": r"\b(?:pcs?|computador(?:a|as|es)?|ordenador(?:a|as|es)?)\b",
    "projector": r"\b(?:proyector(?:es)?|projectors?)\b",
    "whiteboard": r"\b(?:pizarras?|whiteboards?)\b",
    "wifi": r"\bwi[ -]?fi\b",
}


def explicit_constraints(text: str, day: date, slot_id: str) -> tuple[str | None, set[str], str | None]:
    if re.search(r"\b(?:dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|[2-9]\d*)\s+(?:salas?|ambientes?|espacios?)\b|\b(?:salas|ambientes)\b", text, re.I):
        return None, set(), "El flujo actual propone una sola sala por solicitud. Solicita cada sala por separado."
    # Bind exclusion language to a room mention; a conversational "No," is separate.
    room_reference = r"(?:(?:la\s+)?(?:sala|ambiente)\s+)?R\d+\b"
    excluded_room = re.search(
        rf"\b(?:no\s+(?:(?:quiero|deseo|necesito|prefiero|reservar|uses|usar|elijas|selecciones)\s+)?|"
        rf"(?:excepto|menos|salvo|evita|evitar|excluye|excluir|descarta|descartar)\s+){room_reference}",
        text, re.I)
    if excluded_room or re.search(r"\bR\d+\s+(?:no\b|queda\s+excluid[oa]\b)", text, re.I):
        return None, set(), "El asistente todavía no admite excluir salas mediante texto libre. Reformula la búsqueda indicando una sala deseada o sin exclusiones."
    rooms = set(re.findall(r"\bR\d+\b", text, re.I))
    rooms = {room.upper() for room in rooms}
    if len(rooms) > 1 or (rooms and not rooms.issubset(ROOM_IDS)):
        return None, set(), "Indica una sola sala existente."
    room = next(iter(rooms), None)
    # The selected date is authoritative; dates written in text need explicit confirmation.
    if re.search(r"\b(?:\d{1,4}[-/]\d{1,2}(?:[-/]\d{1,4})?|\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)|hoy|mañana|pasado mañana|lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b", text, re.I):
        return room, set(), "Comprueba la fecha escrita y ajusta el selector de fecha; evita repetirla en el texto."
    times = re.findall(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)", text)
    if times:
        expected_start, expected_end = SLOTS[slot_id]
        try:
            parsed = [time(int(h), int(m)) for h, m in times]
        except ValueError:
            return room, set(), "La hora indicada no es válida."
        interval = re.search(r"\b\d{1,2}:\d{2}\s*(?:a|hasta|[-–])\s*(?:las\s+)?\d{1,2}:\d{2}\b", text, re.I)
        if parsed != [expected_start] and not (parsed == [expected_start, expected_end] and interval):
            return room, set(), "La hora escrita no coincide con la franja seleccionada o excede una franja; ajusta el selector."
    elif re.search(r"\b(?:a las|desde las|hasta las)\s+\d", text, re.I):
        return room, set(), "Indica la hora con formato HH:MM y selecciona una franja compatible."
    required = {key for key, pattern in EQUIPMENT_ALIASES.items() if re.search(pattern, text, re.I)}
    if required and re.search(r"\b(?:sin|no|opcional(?:es)?|opcionalmente|preferib(?:le|lemente)|si es posible|o|u|alternativa(?:s)?)\b", text, re.I):
        return room, required, "Aclara qué equipos son obligatorios, sin negaciones ni alternativas."
    return room, required, None


def clarification(message: str) -> dict:
    return {"status": "needs_clarification", "message": message, "proposal": None, "tool_trace": []}


@app.post("/api/assistant/propose")
def propose(payload: AssistantIn):
    day = date.fromisoformat(payload.date)
    if not date_allowed(day):
        raise APIError(422, "invalid_date", "La fecha debe estar entre hoy y los próximos 7 días.", ["date"])
    if not slot_not_started(day, payload.slot_id):
        raise APIError(422, "invalid_slot", "La franja ya comenzó; elige otra.", ["slot_id"])
    if re.search(r"(?:[¿]\s*)?\b(?:qué|cuál|cuáles|cuánto|cuánta|cuántos|cuántas|cómo|dime|información|informacion)\b", payload.text, re.IGNORECASE):
        return clarification("Las consultas informativas aún no están disponibles en el asistente; revisa el catálogo de salas.")
    room, explicit_equipment, issue = explicit_constraints(payload.text, day, payload.slot_id)
    if issue:
        return clarification(issue)
    attendees = assistant_attendees(payload.text)
    if attendees is None:
        return clarification("Indica una cantidad única de asistentes entre 1 y 100, por ejemplo: 6 personas.")
    if not os.getenv("DEEPSEEK_API_KEY"):
        raise APIError(503, "assistant_unavailable", "Asistente sin configurar; usa el formulario.")
    try:
        raw = deepseek.call_tool("search_rooms", SEARCH_SCHEMA,
            f"Solicitud: {payload.text}\nFecha: {payload.date}; franja: {payload.slot_id}; asistentes: {attendees}. "
            "Equipos permitidos: pc, projector, whiteboard, wifi. No inventes requisitos.")
        search = SearchArgs.model_validate(raw)
        required = search.required_equipment
        if set(required) != explicit_equipment:
            return clarification("No se pudieron verificar los equipos solicitados. Reformula los requisitos e inténtalo de nuevo.")
        if (search.date != payload.date or search.slot_id != payload.slot_id
                or search.attendees != attendees or len(required) != len(set(required))
                or not set(required).issubset(EQUIPMENT)):
            raise ValueError("invalid search")
        candidates = room_candidates(payload.date, payload.slot_id, attendees, required)
        if room:
            candidates = [candidate for candidate in candidates if candidate["room_id"] == room]
        if not candidates:
            return {"status": "no_match", "message": f"No hay coincidencias para {room} en esa franja." if room else "No hay una sala compatible para esa franja.",
                    "proposal": None, "tool_trace": ["search_rooms"]}
        raw_proposal = deepseek.call_tool("propose_reservation", PROPOSAL_SCHEMA,
            "Selecciona y copia exactamente una candidata validada: " + json.dumps(candidates))
        selected = ProposalArgs.model_validate(raw_proposal).model_dump()
        if selected not in candidates:
            raise ValueError("invalid proposal")
        # Revalidate availability after the provider call; proposals never write reservations.
        if selected not in room_candidates(payload.date, payload.slot_id, attendees, required):
            return {"status": "no_match", "message": "La sala ya no está disponible; consulta de nuevo.",
                    "proposal": None, "tool_trace": ["search_rooms", "propose_reservation"]}
        return {"status": "proposed", "message": "Opción compatible con los asistentes y equipos solicitados. Revisa y confirma.",
                "proposal": selected, "tool_trace": ["search_rooms", "propose_reservation"]}
    except Exception:
        raise APIError(503, "assistant_unavailable", "No se pudo consultar DeepSeek; usa el formulario.") from None


@app.post("/api/telemetry", status_code=202)
def post_telemetry(payload: TelemetryIn, authorization: str | None = Header(default=None)):
    secret = os.getenv("VISION_INGEST_TOKEN")
    if not secret or authorization != f"Bearer {secret}":
        raise APIError(401, "telemetry_unauthorized", "Token de ingesta inválido.")
    received = now_utc()
    age = (received - payload.observed_at).total_seconds()
    if age > 15 or age < -5:
        raise APIError(422, "telemetry_time_invalid", "Medición fuera de la ventana temporal.", ["observed_at"])
    previous = last_sample()
    if previous and payload.observed_at <= previous["observed_at"]:
        raise APIError(409, "telemetry_out_of_order", "Medición anterior a la última aceptada.", ["observed_at"])
    expires = min(payload.observed_at + timedelta(seconds=15), received + timedelta(seconds=15))
    app.state.last_telemetry = {"source_id": payload.source_id, "room_id": payload.room_id,
        "mode": payload.mode, "status": payload.status, "count": payload.count,
        "observed_at": payload.observed_at, "received_at": received, "expires_at": expires}
    return {"accepted": True, "room_id": payload.room_id,
        "received_at": received.isoformat().replace("+00:00", "Z"),
        "expires_at": expires.isoformat().replace("+00:00", "Z")}


FRONTEND_DIST = ROOT / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
