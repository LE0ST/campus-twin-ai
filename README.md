# CampusTwin AI — QuantumByte

Prototipo de planificación de espacios con catálogo y reservas de demostración. Los ambientes y sus datos son sintéticos; no representan disponibilidad ni aforo real de la UNMSM.

## Requisitos

- Python 3.12 o compatible con las dependencias indicadas.
- Node.js con npm.

## Ejecutar en desarrollo

En la raíz del repositorio, instala y arranca el backend:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt httpx pytest
Copy-Item .env.example .env
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Abre la URL local que muestre Vite. Su proxy `/api` apunta al backend en `127.0.0.1:8000` por defecto. Para cambiarlo, define `CAMPUSTWIN_API_TARGET` al iniciar Vite.

## Servir la compilación desde FastAPI

```powershell
cd frontend
npm ci
npm run build
cd ..
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

FastAPI sirve `frontend/dist` cuando existe. La base SQLite local se crea en `backend/campustwin.db` y está excluida de Git.

## Configuración opcional

- `DEEPSEEK_API_KEY`: activa las propuestas del asistente DeepSeek Flash. Sin la clave, el formulario de reserva sigue disponible.
- `DEEPSEEK_MODEL`: modelo configurable; por defecto `deepseek-flash`.
- `VISION_INGEST_TOKEN`: habilita la ingesta autenticada del servicio de visión.
- `CAMPUSTWIN_DB`: ruta alternativa para la base SQLite.

Configura estos valores solo en `.env` local o en el entorno del proceso. Nunca publiques claves. La telemetría de una grabación autorizada se presenta como muestra registrada, no como ocupación actual.

El backend lee variables del entorno del proceso; copiar `.env.example` a `.env` no las carga automáticamente. En PowerShell configura la clave localmente en la sesión antes de arrancar el servidor. `/api/health` indica si hay clave configurada, pero no comprueba acceso ni cuota de DeepSeek. El SDK `openai` tiene licencia Apache-2.0.

## Compatibilidad de integración revisada

Se revisaron los consumidores publicados en `frontend/catalogo-estados` (`de36bf2`) y `vision` (`7ea4c18`). La agenda de Secretaría consulta las ocho franjas con `GET /api/rooms`; las reservas usan `POST /api/reservations` con confirmación humana. El asistente conserva `text`, `date`, `slot_id`, `proposal`, `message` y `tool_trace`. El cliente de visión envía las mediciones a `POST /api/telemetry` con Bearer token.

La revisión aislada comprobó el envío del cliente HTTP de David a FastAPI y la lectura de las respuestas por las funciones de agenda y ocupación de Marco. No ejecutó cámara/GPU ni reemplaza un ensayo conjunto por LAN. No incluye solicitudes pendientes, aprobaciones, autenticación administrativa ni correos.

Para activar este backend más adelante, durante una ventana acordada con el equipo, inicia Uvicorn desde la copia integrada con `--host 0.0.0.0 --port 8000 --env-file .env`. No inicies un segundo escritor sobre la base del servidor activo.

## Verificación

```powershell
.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
```
