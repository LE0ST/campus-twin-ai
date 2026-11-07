import logging
import time
import numpy as np
from typing import Tuple, Optional
from ultralytics import YOLO

logger = logging.getLogger("vision.detector")


class PersonDetector:
    """Detector de personas basado en YOLO11n optimizado para RTX 4060 / CPU."""

    def __init__(self, weights_path: str, device: str = "cuda:0", imgsz: int = 640, conf_threshold: float = 0.35):
        self.weights_path = weights_path
        self.imgsz = imgsz
        self.conf_threshold = conf_threshold
        self.device = device
        self.model: Optional[YOLO] = None
        self._load_model()

    def _load_model(self):
        logger.info(f"Cargando modelo YOLO11n desde: {self.weights_path}")
        try:
            self.model = YOLO(self.weights_path)
            # Intento de inferencia en dispositivo solicitado
            logger.info(f"Configurando dispositivo: {self.device}")
            # Warm-up rápido para inicializar pesos y CUDA context
            dummy = np.zeros((self.imgsz, self.imgsz, 3), dtype=np.uint8)
            self.model(dummy, device=self.device, classes=[0], imgsz=self.imgsz, verbose=False)
            logger.info(f"Detector inicializado exitosamente en {self.device}")
        except Exception as e:
            if self.device != "cpu":
                logger.warning(f"Fallo al inicializar en {self.device}: {e}. Intentando fallback a CPU...")
                self.device = "cpu"
                dummy = np.zeros((self.imgsz, self.imgsz, 3), dtype=np.uint8)
                self.model(dummy, device="cpu", classes=[0], imgsz=self.imgsz, verbose=False)
                logger.info("Detector inicializado exitosamente en CPU (fallback)")
            else:
                logger.error(f"Error fatal inicializando detector YOLO en CPU: {e}")
                raise

    def count_persons(self, frame: np.ndarray, return_annotated: bool = False) -> Tuple[int, float, Optional[np.ndarray]]:
        """
        Ejecuta inferencia exclusivamente sobre clase 0 (person).
        Retorna (count: int, latency_ms: float, annotated_frame: Optional[np.ndarray]).
        count está estrictamente acotado en [0, 100].
        No guarda imágenes en disco ni realiza biometría.
        """
        if self.model is None or frame is None:
            raise RuntimeError("Modelo no cargado o frame inválido")

        t_start = time.perf_counter()

        # Inferencia exclusiva en personas (classes=[0])
        results = self.model(
            frame,
            device=self.device,
            classes=[0],
            imgsz=self.imgsz,
            conf=self.conf_threshold,
            verbose=False,
        )

        latency_ms = (time.perf_counter() - t_start) * 1000.0

        if not results or len(results) == 0:
            return 0, latency_ms, frame if return_annotated else None

        boxes = results[0].boxes
        raw_count = len(boxes) if boxes is not None else 0

        # Límite de integridad contractual: entero en [0, 100]
        final_count = min(max(int(raw_count), 0), 100)

        annotated_frame = results[0].plot() if return_annotated else None

        return final_count, latency_ms, annotated_frame
