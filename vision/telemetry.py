import logging
import requests
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("vision.telemetry")


class TelemetryClient:
    """Cliente HTTP estricto conforme a API_CONTRACT.md v1.0."""

    def __init__(self, backend_url: str, token: Optional[str], source_id: str = "vision-david", room_id: str = "R01"):
        self.endpoint = f"{backend_url.rstrip('/')}/api/telemetry"
        self.token = token
        self.source_id = source_id
        self.room_id = room_id
        self._last_observed_at: Optional[str] = None

    def send_telemetry(
        self,
        mode: str,
        status: str,
        count: Optional[int],
        observed_at: str,
    ) -> Tuple[bool, int, Optional[Dict[str, Any]]]:
        """
        Envía telemetría cerrada al backend.
        No encola reintentos (política estricta de descarte de backlog).
        Retorna (success: bool, http_code: int, response_json: Optional[dict]).
        """
        # Validación interna de reglas antes de enviar
        if status == "error":
            payload_count = None
        else:
            if count is None:
                raise ValueError("status 'ok' requiere count numérico")
            payload_count = min(max(int(count), 0), 100)

        # Esquema JSON cerrado: prohibido añadir campos extra
        payload = {
            "source_id": self.source_id,
            "room_id": self.room_id,
            "mode": mode,
            "status": status,
            "count": payload_count,
            "observed_at": observed_at,
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            # Timeout corto para no retrasar la cadencia de 3s
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=2.5)
            self._last_observed_at = observed_at

            if response.status_code == 202:
                logger.info(
                    f"Telemetría ACEPTADA (202): status={status}, count={payload_count}, mode={mode}, observed_at={observed_at}"
                )
                try:
                    return True, 202, response.json()
                except Exception:
                    return True, 202, None
            else:
                logger.warning(
                    f"Telemetría RECHAZADA ({response.status_code}): {response.text[:200]}"
                )
                try:
                    return False, response.status_code, response.json()
                except Exception:
                    return False, response.status_code, None

        except requests.exceptions.Timeout:
            logger.error("Timeout de red (>2.5 s) enviando telemetría hacia el backend. Descartando muestra.")
            return False, 504, None
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión con el backend (servidor caído o ruta no alcanzable). Descartando muestra.")
            return False, 503, None
        except Exception as e:
            logger.error(f"Error inesperado al emitir telemetría: {e}")
            return False, 500, None
