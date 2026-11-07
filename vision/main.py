import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone

# Asegurar que la carpeta vision/ esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import parse_args
from camera import VideoSource
from detector import PersonDetector
from telemetry import TelemetryClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("vision.main")

_running = True


def handle_sigint(signum, frame):
    global _running
    logger.info("Señal de interrupción recibida (Ctrl+C). Deteniendo módulo de visión...")
    _running = False


signal.signal(signal.SIGINT, handle_sigint)
signal.signal(signal.SIGTERM, handle_sigint)


def run_pipeline():
    global _running
    config = parse_args()

    logger.info("=== QuantumByte / CampusTwin AI - Módulo Visión (David Yalle) ===")
    logger.info(f"Modo: {config.mode} | Sala: {config.room_id} | Fuente: {config.source_id}")
    logger.info(f"Backend: {config.backend_url} | Dispositivo: {config.device}")
    logger.info(f"Cadencia: {config.cadence_seconds} s | Umbral conf: {config.conf_threshold}")

    # Inicializar cliente de telemetría
    telemetry = TelemetryClient(
        backend_url=config.backend_url,
        token=config.token,
        source_id=config.source_id,
        room_id=config.room_id,
    )

    # Inicializar detector YOLO11n
    try:
        detector = PersonDetector(
            weights_path=config.weights,
            device=config.device,
            imgsz=config.imgsz,
            conf_threshold=config.conf_threshold,
        )
    except Exception as e:
        logger.error(f"Error crítico al inicializar PersonDetector: {e}")
        # Notificar error al backend antes de terminar si es posible
        err_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        telemetry.send_telemetry(mode=config.mode, status="error", count=None, observed_at=err_time)
        return

    # Inicializar captura de video
    video = VideoSource(
        camera_index=config.camera_index,
        clip_path=config.clip_path,
    )

    if not video.open():
        logger.error("No se pudo iniciar la captura de video. Enviando status=error al backend...")
        err_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        telemetry.send_telemetry(mode=config.mode, status="error", count=None, observed_at=err_time)
        return

    logger.info(f"Iniciando ciclo continuo de telemetría cada {config.cadence_seconds} segundos...")

    try:
        while _running:
            tick_start = time.perf_counter()

            success, frame, observed_at = video.read_frame()

            if not success or frame is None or observed_at is None:
                logger.warning("Fallo en captura de fotograma. Emitiendo status=error...")
                err_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                telemetry.send_telemetry(
                    mode=config.mode,
                    status="error",
                    count=None,
                    observed_at=err_time,
                )
            else:
                try:
                    count, lat_ms = detector.count_persons(frame)
                    logger.info(
                        f"[FRAME] count={count} personas detectadas | latencia={lat_ms:.1f} ms | observed_at={observed_at}"
                    )
                    telemetry.send_telemetry(
                        mode=config.mode,
                        status="ok",
                        count=count,
                        observed_at=observed_at,
                    )
                except Exception as e:
                    logger.error(f"Error durante inferencia: {e}. Emitiendo status=error...")
                    err_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    telemetry.send_telemetry(
                        mode=config.mode,
                        status="error",
                        count=None,
                        observed_at=err_time,
                    )

            # Control preciso de cadencia de 3 segundos
            elapsed = time.perf_counter() - tick_start
            sleep_time = max(0.0, config.cadence_seconds - elapsed)

            # Dormir en micro-intervalos para responder rápido a Ctrl+C
            sleep_step = 0.1
            while _running and sleep_time > 0:
                time.sleep(min(sleep_step, sleep_time))
                sleep_time -= sleep_step

    finally:
        logger.info("Cerrando recursos de visión...")
        video.release()
        logger.info("Módulo de visión finalizado de forma limpia.")


if __name__ == "__main__":
    run_pipeline()
