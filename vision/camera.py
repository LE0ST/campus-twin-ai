import cv2
import logging
import platform
import numpy as np
from datetime import datetime, timezone
from typing import Optional, Tuple

logger = logging.getLogger("vision.camera")


class VideoSource:
    """Manejo de captura de cámara USB o clip de respaldo autorizado."""

    def __init__(self, camera_index: int = 1, clip_path: Optional[str] = None):
        self.camera_index = camera_index
        self.clip_path = clip_path
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_clip = clip_path is not None

    def open(self) -> bool:
        """Abre el stream de captura."""
        if self.is_clip:
            logger.info(f"Abriendo clip de video autorizado: {self.clip_path}")
            self.cap = cv2.VideoCapture(self.clip_path)
        else:
            logger.info(f"Abriendo webcam USB en índice {self.camera_index}")
            # En Windows cv2.CAP_DSHOW previene cuelgues de Media Foundation
            if platform.system() == "Windows":
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap or not self.cap.isOpened():
            logger.error(f"No se pudo abrir el dispositivo/archivo de video (índice={self.camera_index}, clip={self.clip_path})")
            return False

        # Configuración de resolución sugerida (640x480)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        logger.info("Dispositivo de video abierto y configurado correctamente.")
        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray], Optional[str]]:
        """
        Lee el frame más reciente y captura observed_at en UTC estricto con 'Z'.
        Retorna (success: bool, frame: Optional[np.ndarray], observed_at_utc: Optional[str]).
        """
        if not self.cap or not self.cap.isOpened():
            return False, None, None

        ret, frame = self.cap.read()

        # En live_camera y en clip, observed_at es la hora UTC exacta de captura/lectura del frame
        observed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if not ret or frame is None:
            if self.is_clip:
                # Si el clip termina, rebobinar al inicio para pruebas continuas
                logger.info("Fin de clip alcanzado, reiniciando reproducción...")
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    return True, frame, observed_at
            logger.warning("Fallo en cap.read() (desconexión o frame corrupto)")
            return False, None, None

        return True, frame, observed_at

    def release(self):
        """Libera el recurso de video de forma segura."""
        if self.cap:
            try:
                self.cap.release()
            except Exception as e:
                logger.warning(f"Error liberando VideoCapture: {e}")
            finally:
                self.cap = None
        logger.info("Recurso de video liberado.")
