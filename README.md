# CampusTwin AI · QuantumByte

Prototipo académico independiente para consultar ambientes y registrar reservas de demostración. No es una plataforma oficial ni un canal institucional de la Universidad Nacional Mayor de San Marcos. Los ambientes y reservas son ficticios; la telemetría física experimental, cuando exista, se identifica por separado.

El frontend React consulta FastAPI, que valida y escribe reservas en SQLite local. DeepSeek Flash propone, sin escribir; la confirmación humana precede al registro. El módulo de visión opcional envía conteos anónimos, sin guardar imágenes. Una lectura ausente, vencida o con error es desconocida; cero detecciones no demuestra ausencia.

## Requisitos y ejecución local

Python 3.12, Node.js y npm compatibles con `frontend/package-lock.json`. En una terminal desde la raíz:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:CAMPUSTWIN_DB = 'backend/campustwin.db'
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

En otra terminal: `cd frontend`, `npm ci`, `npm run dev`. Vite dirige `/api` a 127.0.0.1:8000 por defecto; `CAMPUSTWIN_API_TARGET` cambia el destino al iniciar Vite. Para servir el build desde FastAPI: `cd frontend; npm ci; npm run build`, luego arrancar FastAPI desde la raíz. Mantener un único escritor SQLite y nunca compartir por red un archivo SQLite abierto.

`.env.example` enumera nombres y ejemplos no secretos. El backend lee el entorno del proceso: copiar un archivo `.env` no lo carga por sí solo. `DEEPSEEK_API_KEY` habilita propuestas; sin ella el asistente funciona en modo degradado. `DEEPSEEK_MODEL` selecciona el modelo. `VISION_INGEST_TOKEN` protege la ingesta y debe coincidir con el agente autorizado; no copiar tokens entre entornos. Para visión y dependencias opcionales consultar [vision/README.md](vision/README.md). No colocar claves en Vite, Git o capturas.

## Demo y límites

Consultar [recorrido de demostración](docs/DEMO.md), [arquitectura](docs/ARCHITECTURE.md), [trazabilidad](docs/TRACEABILITY.md) y [QA](docs/QA_REPORT.md). Los perfiles son visuales, sin autenticación ni permisos reales. Las propuestas deben revisarse y confirmarse. Sin lectura autorizada y vigente se muestra ocupación desconocida. No se ha acreditado en este QA una llamada real a DeepSeek ni inferencia real de YOLO. El despliegue público no está verificado.

Pruebas locales: `.venv\Scripts\python.exe -m pytest tests -q`; en `frontend`, `npm test`, `npm run lint`, `npm run build`. Los tests deben usar una base aislada y proveedor simulado.
