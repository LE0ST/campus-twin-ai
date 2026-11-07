# Trazabilidad

| Requisito | Implementación | Evidencia y resultado |
|---|---|---|
| Catálogo ficticio y perfiles | `frontend/src/components/DashboardLayout.jsx`, `backend/main.py` | Revisión visual y navegación parcial; no autentica. |
| Reserva y confirmación | `POST /api/reservations`, `frontend/src/App.jsx` | QA aislado: 201; mismo request_id 200; conflicto 409; agenda visible. |
| Asistente con herramientas restringidas | `backend/deepseek.py`, `POST /api/assistant/propose`, `tests/test_assistant_validation.py` | Tests con proveedor simulado; DeepSeek real no acreditado. |
| T31 caducidad | `frontend/src/catalogLifetime.js`, `backend/main.py` | TestClient aislado: 202, people_detected, unknown/stale a 16,03 s; frontend automático pasa, ensayo visual integrado pendiente. |
| T53 reactivación | `frontend/src/catalogLifetime.js`, `frontend/tests/catalogLifetime.test.mjs` | Evidencia de QA proporcionada: hidden→visible 26,28 s, GET 86,4 ms después. |
| Identidad independiente | `frontend/src/components/ProfileChooser.jsx`, `DashboardLayout.jsx` | Avisos visibles; SVG institucional retirado. |
| Visión YOLO | `vision/` y `POST /api/telemetry` | Integrado en código; cámara e inferencia reales no acreditadas en este QA. |
