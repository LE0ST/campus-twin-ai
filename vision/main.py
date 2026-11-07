import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone
import cv2

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

    logger.info(f"Iniciando captura en tiempo real con emisión de telemetría cada {config.cadence_seconds} s...")

    last_telemetry_time = 0.0

    def async_send(mode, status, count, observed_at):
        telemetry.send_telemetry(mode=mode, status=status, count=count, observed_at=observed_at)

    try:
        while _running:
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
                time.sleep(0.5)
                continue

            # Inferencia YOLO en el frame actual (RTX 4060 corre en ~25ms fluidamente)
            try:
                count, lat_ms, annotated = detector.count_persons(frame, return_annotated=config.show)
            except Exception as e:
                logger.error(f"Error durante inferencia: {e}")
                count, lat_ms, annotated = 0, 0.0, frame if config.show else None

            # Envío de telemetría exactamente cada 3.0 segundos
            now = time.perf_counter()
            if now - last_telemetry_time >= config.cadence_seconds:
                last_telemetry_time = now
                logger.info(
                    f"[TELEMETRIA] count={count} personas | latencia_gpu={lat_ms:.1f} ms | observed_at={observed_at}"
                )
                # Enviar de forma asíncrona para no congelar la ventana de video
                t = threading.Thread(
                    target=async_send,
                    args=(config.mode, "ok", count, observed_at),
                    daemon=True,
                )
                t.start()

            # Si --show está activo, renderizar video fluido en tiempo real
            if config.show and annotated is not None:
                cv2.putText(
                    annotated,
                    f"CampusTwin R01 | Count: {count} | GPU: {lat_ms:.1f}ms",
                    (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow("CampusTwin AI - Monitor de Vision (Local)", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    _running = False
                    break
            elif not config.show:
                # Si es headless, un micro-sleep para no saturar CPU innecesariamente
                time.sleep(0.01)

    finally:
        logger.info("Cerrando recursos de visión...")
        video.release()
        if config.show:
            cv2.destroyAllWindows()
        logger.info("Módulo de visión finalizado de forma limpia.")


if __name__ == "__main__":
    run_pipeline()
