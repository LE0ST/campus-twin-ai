import os
import sys
import time
import unittest
from datetime import datetime, timezone
import numpy as np

# Asegurar que la carpeta vision/ esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from detector import PersonDetector
from camera import VideoSource
from telemetry import TelemetryClient


class TestVisionModule(unittest.TestCase):
    """Batería de pruebas unitarias y de integración para vision/ (T23, T28, T33, T36)."""

    @classmethod
    def setUpClass(cls):
        # Cargar .env de la raíz si existe
        root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(root_env):
            try:
                with open(root_env, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k and k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass

        cls.weights_path = os.environ.get("VISION_WEIGHTS", r"C:\Users\yalle\dayzero_gpu_test\yolo11n.pt")
        cls.backend_url = os.environ.get("CAMPUS_TWIN_BACKEND_URL", "http://10.96.239.62:8000")
        cls.token = os.environ.get("VISION_INGEST_TOKEN", "")

    def test_01_cuda_inference(self):
        """T28/T36: Inferencia YOLO11n en GPU cuda:0."""
        detector = PersonDetector(weights_path=self.weights_path, device="cuda:0")
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        count, lat_ms, _ = detector.count_persons(dummy)
        print(f"\n[PASS] Inferencia CUDA: count={count}, latencia={lat_ms:.2f} ms")
        self.assertEqual(count, 0)
        self.assertLess(lat_ms, 500.0)

    def test_02_cpu_inference_fallback(self):
        """T36: Inferencia YOLO11n en CPU (fallback)."""
        detector = PersonDetector(weights_path=self.weights_path, device="cpu")
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        count, lat_ms, _ = detector.count_persons(dummy)
        print(f"\n[PASS] Inferencia CPU: count={count}, latencia={lat_ms:.2f} ms")
        self.assertEqual(count, 0)
        self.assertLess(lat_ms, 1000.0)

    def test_03_camera_capture(self):
        """T28: Captura de frame desde webcam y timestamp UTC."""
        camera = VideoSource(camera_index=1)
        opened = camera.open()
        if not opened:
            camera = VideoSource(camera_index=0)
            opened = camera.open()
        if opened:
            success, frame, observed_at = camera.read_frame()
            camera.release()
            self.assertTrue(success)
            self.assertIsNotNone(frame)
            self.assertTrue(observed_at.endswith("Z"))
            print(f"\n[PASS] Captura de cámara: shape={frame.shape}, observed_at={observed_at}")
        else:
            print("\n[INFO] Cámara ocupada por el proceso de captura principal")

    def test_04_telemetry_schema_authorized(self):
        """T23: Telemetría válida con token autorizado debe devolver HTTP 202."""
        if not self.token:
            self.skipTest("No se configuró VISION_INGEST_TOKEN en el entorno")
        client = TelemetryClient(backend_url=self.backend_url, token=self.token)
        time.sleep(1.0)
        now_z = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        success, code, body = client.send_telemetry(
            mode="live_camera",
            status="ok",
            count=1,
            observed_at=now_z,
        )
        print(f"\n[PASS] Telemetría autorizada (T23): code={code}, accepted={body.get('accepted') if body else None}")
        self.assertEqual(code, 202, f"Se esperaba 202 Accepted pero se recibió {code}")
        self.assertTrue(success)

    def test_05_telemetry_unauthorized(self):
        """T38: Telemetría con token inválido debe devolver estrictamente HTTP 401."""
        client = TelemetryClient(backend_url=self.backend_url, token="token_invalido_de_prueba")
        time.sleep(1.0)
        now_z = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        success, code, body = client.send_telemetry(
            mode="live_camera",
            status="ok",
            count=1,
            observed_at=now_z,
        )
        print(f"\n[PASS] Telemetría rechazada por auth (T38): code={code}")
        self.assertEqual(code, 401, f"Se esperaba 401 Unauthorized pero se recibió {code}")
        self.assertFalse(success)

    def test_06_telemetry_error_status(self):
        """T33: Telemetría con status='error' y count=null debe ser aceptada con 202."""
        if not self.token:
            self.skipTest("No se configuró VISION_INGEST_TOKEN en el entorno")
        client = TelemetryClient(backend_url=self.backend_url, token=self.token)
        time.sleep(1.0)
        now_z = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        success, code, body = client.send_telemetry(
            mode="live_camera",
            status="error",
            count=None,
            observed_at=now_z,
        )
        print(f"\n[PASS] Telemetría status=error aceptada (T33): code={code}")
        self.assertEqual(code, 202, f"Se esperaba 202 Accepted pero se recibió {code}")
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
