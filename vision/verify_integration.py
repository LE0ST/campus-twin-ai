import os
import sys
from datetime import datetime, timezone
import requests

def test_integration(token: str, backend_url: str = "http://10.96.239.62:8000"):
    print(f"=== PRUEBA DE INTEGRACIÓN DE VISIÓN (David -> Leonardo) ===")
    print(f"Backend URL: {backend_url}")
    print(f"Token: {'*' * len(token) if token else '[VACÍO]'}\n")

    # 1. Comprobar solicitud HTTP al backend (/api/health)
    print("1. Probando GET /api/health...")
    try:
        r_health = requests.get(f"{backend_url}/api/health", timeout=3.0)
        print(f"   Status: {r_health.status_code}")
        print(f"   Respuesta: {r_health.text}")
        if r_health.status_code != 200:
            print("   [FALLO] No se obtuvo 200 OK en /api/health")
            return False
        print("   [ÉXITO] Conexión HTTP al backend comprobada correctamente.\n")
    except Exception as e:
        print(f"   [ERROR] No se pudo conectar al backend: {e}")
        return False

    # 2. Probar endpoint de telemetría (/api/telemetry)
    print("2. Probando POST /api/telemetry...")
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    test_count = 2
    payload = {
        "source_id": "vision-david",
        "room_id": "R01",
        "mode": "live_camera",
        "status": "ok",
        "count": test_count,
        "observed_at": now_utc
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        r_telem = requests.post(f"{backend_url}/api/telemetry", json=payload, headers=headers, timeout=3.0)
        print(f"   Status: {r_telem.status_code}")
        print(f"   Respuesta: {r_telem.text}")

        if r_telem.status_code == 401:
            print("   [BLOQUEO] 401 Unauthorized: El token de ingesta no coincide con el configurado en Leonardo.")
            return False
        elif r_telem.status_code != 202:
            print(f"   [FALLO] Esperaba 202 Accepted, recibido {r_telem.status_code}")
            return False
        print("   [ÉXITO] Telemetría aceptada por el backend con código 202 Accepted.\n")
    except Exception as e:
        print(f"   [ERROR] Fallo al emitir telemetría: {e}")
        return False

    # 3. Verificar que conteo y timestamp llegan correctamente a /api/rooms
    print("3. Verificando conteo y timestamp en GET /api/rooms...")
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        r_rooms = requests.get(f"{backend_url}/api/rooms", params={"date": today_str, "slot_id": "S18"}, timeout=3.0)
        print(f"   Status: {r_rooms.status_code}")
        if r_rooms.status_code != 200:
            print(f"   [FALLO] No se pudo consultar /api/rooms ({r_rooms.status_code})")
            return False

        data = r_rooms.json()
        r01 = next((r for r in data.get("rooms", []) if r.get("room_id") == "R01"), None)
        if not r01:
            print("   [FALLO] Sala R01 no encontrada en la respuesta de /api/rooms")
            return False

        occ = r01.get("occupancy", {})
        print(f"   Occupancy en R01: state={occ.get('state')}, count={occ.get('count')}, observed_at={occ.get('observed_at')}")
        
        # Validar count
        if occ.get("count") == test_count and occ.get("state") == "people_detected":
            print(f"   [ÉXITO] El conteo llegó correctamente: count={test_count}, state=people_detected")
        else:
            print(f"   [FALLO] El conteo no coincide: esperado {test_count}, recibido {occ.get('count')}")
            return False

        # Validar timestamp
        if occ.get("observed_at") and occ.get("observed_at").startswith(now_utc[:19]):
            print(f"   [ÉXITO] El timestamp observed_at llegó correctamente: {occ.get('observed_at')}\n")
        else:
            print(f"   [ADVERTENCIA] Timestamp difiere ligeramente o formato distinto: enviado {now_utc}, recibido {occ.get('observed_at')}")

        print("=== RESULTADO: INTEGRACIÓN DE VISIÓN COMPLETADA AL 100% ===")
        return True
    except Exception as e:
        print(f"   [ERROR] Error consultando /api/rooms: {e}")
        return False

if __name__ == "__main__":
    tok = os.environ.get("VISION_INGEST_TOKEN", "").strip()
    if len(sys.argv) > 1:
        tok = sys.argv[1].strip()
    
    backend = os.environ.get("CAMPUS_TWIN_BACKEND_URL", "http://10.96.239.62:8000")
    if len(sys.argv) > 2:
        backend = sys.argv[2].strip()

    test_integration(tok, backend)
