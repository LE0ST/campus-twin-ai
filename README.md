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

- `GEMINI_API_KEY`: activa las propuestas del asistente Gemini. Sin la clave, el formulario de reserva sigue disponible.
- `GEMINI_MODEL`: modelo configurable; por defecto `gemini-3.5-flash-lite`.
- `VISION_INGEST_TOKEN`: habilita la ingesta autenticada del servicio de visión.
- `CAMPUSTWIN_DB`: ruta alternativa para la base SQLite.

Configura estos valores solo en `.env` local o en el entorno del proceso. Nunca publiques claves. La telemetría de una grabación autorizada se presenta como muestra registrada, no como ocupación actual.

## Verificación

```powershell
.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
```
