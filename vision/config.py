import argparse
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class VisionConfig:
    backend_url: str
    token: Optional[str]
    camera_index: int
    clip_path: Optional[str]
    device: str
    weights: str
    source_id: str = "vision-david"
    room_id: str = "R01"
    mode: str = "live_camera"
    cadence_seconds: float = 3.0
    imgsz: int = 640
    conf_threshold: float = 0.35


def parse_args() -> VisionConfig:
    parser = argparse.ArgumentParser(description="CampusTwin AI - Módulo de Visión (David Yalle)")
    parser.add_argument(
        "--backend",
        type=str,
        default=os.environ.get("CAMPUS_TWIN_BACKEND_URL", "http://10.96.239.62:8000"),
        help="URL base del backend de Leonardo (ej. http://10.96.239.62:8000)",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=os.environ.get("VISION_INGEST_TOKEN", ""),
        help="Token Bearer de ingesta de telemetría (recomendado vía env var VISION_INGEST_TOKEN)",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=int(os.environ.get("VISION_CAMERA_INDEX", "1")),
        help="Índice de la webcam USB (por defecto 1 para EMEET S600)",
    )
    parser.add_argument(
        "--clip",
        type=str,
        default=None,
        help="Ruta a clip de video autorizado (activa mode=authorized_clip)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=os.environ.get("VISION_DEVICE", "cuda:0"),
        help="Dispositivo de inferencia ('cuda:0' por defecto, 'cpu' para fallback)",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=os.environ.get("VISION_WEIGHTS", r"C:\Users\yalle\dayzero_gpu_test\yolo11n.pt"),
        help="Ruta local al modelo YOLO11n (.pt)",
    )
    parser.add_argument(
        "--cadence",
        type=float,
        default=3.0,
        help="Cadencia de telemetría en segundos (3.0 s por contrato)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Resolución de inferencia YOLO (640)",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.35,
        help="Umbral de confianza para clase persona",
    )

    args = parser.parse_args()

    mode = "authorized_clip" if args.clip else "live_camera"
    token = args.token.strip() if args.token else None

    return VisionConfig(
        backend_url=args.backend.rstrip("/"),
        token=token,
        camera_index=args.camera,
        clip_path=args.clip,
        device=args.device,
        weights=args.weights,
        source_id="vision-david",
        room_id="R01",
        mode=mode,
        cadence_seconds=args.cadence,
        imgsz=args.imgsz,
        conf_threshold=args.conf,
    )
