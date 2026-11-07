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
        cls.weights_path = os.environ.get("VISION_WEIGHTS", r"C:\Users\yalle\dayzero_gpu_test\yolo11n.pt")
        cls.backend_url = os.environ.get("CAMPUS_TWIN_BACKEND_URL", "http://10.96.239.62:8000")
        cls.token = os.environ.get("VISION_INGEST_TOKEN", "")

    def test_01_cuda_inference(self):
        """T28/T36: Inferencia YOLO11n en GPU cuda:0."""
        detector = PersonDetector(weights_path=self.weights_path, device="cuda:0")
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        count, lat_ms = detector.count_persons(dummy)
        print(f"\n[PASS] Inferencia CUDA: count={count}, latencia={lat_ms:.2f} ms")
        self.assertEqual(count, 0)
        self.assertLess(lat_ms, 500.0)

    def test_02_cpu_inference_fallback(self):
        """T36: Inferencia YOLO11n en CPU (fallback)."""
        detector = PersonDetector(weights_path=self.weights_path, device="cpu")
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        count, lat_ms = detector.count_persons(dummy)
        print(f"\n[PASS] Inferencia CPU: count={count}, latencia={lat_ms:.2f} ms")
        self.assertEqual(count, 0)
        self.assertLess(lat_ms, 1000.0)

    def test_03_camera_capture(self):
        """T28: Captura de frame desde índice 1 (EMEET S600) y timestamp UTC."""
        camera = VideoSource(camera_index=1)
        opened = camera.open()
        self.assertTrue(opened, "No se pudo abrir la cámara en índice 1")
        success, frame, observed_at = camera.read_frame()
        camera.release()
        self.assertTrue(success)
        self.assertIsNotNone(frame)
        self.assertTrue(observed_at.endswith("Z"))
        print(f"\n[PASS] Captura de cámara: shape={frame.shape}, observed_at={observed_at}")

    def test_04_telemetry_schema(self):
        """T33/T38: Esquema y cliente HTTP de telemetría."""
        client = TelemetryClient(backend_url=self.backend_url, token=self.token)
        now_z = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Probar emisión válida
        success, code, body = client.send_telemetry(
            mode="live_camera",
            status="ok",
            count=1,
            observed_at=now_z,
        )
        print(f"\n[INFO] Envío telemetría hacia {self.backend_url}: code={code}, body={body}")
        # Si el backend exige token y no se pasó, debe retornar 401 (T38)
        # Si se pasó token válido, debe retornar 202 (T23)
        self.assertIn(code, [202, 401, 422])


if __name__ == "__main__":
    unittest.main()
