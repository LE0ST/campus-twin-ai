# CampusTwin AI
### Smart campus room availability, reservations & AI-assisted planning
**QuantumByte · ENEISOFT XVI 2026 · Independent academic prototype**

[**Live demo**](https://campustwin-ai-demo.onrender.com) · [**Architecture**](docs/ARCHITECTURE.md) · [**QA report**](docs/QA_REPORT.md) · [**Demo script**](docs/DEMO.md) · [**Deployment guide**](docs/RENDER_DEPLOY.md)

> **Academic demonstration, not an official UNMSM service.** Rooms, schedules and reservations are fictional. Do not submit personal or institutional data. The role selector is a UI demonstration, **not authentication or authorization**.

## What it does

| Capability | Implementation | Important limitation |
| --- | --- | --- |
| Room catalogue | React + Vite, FastAPI | Fictional room inventory |
| Reservations and Secretary agenda | FastAPI + SQLite | Demo roles do not enforce access permissions |
| AI assistant | DeepSeek Flash proposes structured options; user confirms | Model does not create reservations autonomously; requires API credentials |
| Occupancy | Optional local YOLO11n agent sends anonymous person counts | Camera is **not hosted** on Render; no measurement means **unknown**, not zero |
| Public demo | One Docker service on Render Free | SQLite in `/tmp` is **ephemeral**; cold starts and data loss on restart/suspend/redeploy |

## Architecture

```text
Browser (React/Vite) ---- HTTPS ----> Render Free (FastAPI)
                                        |-- GET /api/health
                                        |-- GET /api/rooms
                                        |-- POST /api/reservations
                                        |-- POST /api/assistant/propose --> DeepSeek (optional)
                                        |-- POST /api/telemetry <--- local YOLO11n + camera
                                        +-- SQLite /tmp (not persistent)
```

The local vision agent transmits numeric counts, timestamps and status only; images are not sent or stored. A measurement expires after approximately 15 seconds. This prototype does not provide institutional booking, identity verification or guaranteed room occupancy.

## Local development (Windows PowerShell)

Requirements: Python 3.12, Node.js compatible with the frontend lockfile, npm.

```powershell
git clone https://github.com/LE0ST/campus-twin-ai.git
cd campus-twin-ai
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

For a single-origin production-like build: `npm run build` inside `frontend/`, then start FastAPI from the repository root. The backend serves `frontend/dist` if present.

## Camera / YOLO agent

The camera runs on the **computer connected to the webcam**, not on Render. Install optional dependencies and YOLO weights as described in [vision/README.md](vision/README.md). In that computer's PowerShell:

```powershell
$env:VISION_INGEST_TOKEN = "<same secret as Render>"
python vision/main.py --backend https://campustwin-ai-demo.onrender.com --camera 1 --device cuda:0 --show
```

Use `--device cpu` when CUDA is unavailable and set `--camera` to the actual webcam index. The `VISION_INGEST_TOKEN` must be set on both sides. Expect HTTP 202 for accepted telemetry; no real camera test is claimed by the repository QA.

## Configuration and security

Set `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `VISION_INGEST_TOKEN`, and `CAMPUSTWIN_DB` as server-side environment variables. Do not commit secrets, expose them to Vite, or paste them into logs. Render Free uses `CAMPUSTWIN_DB=/tmp/campustwin-demo.db` with **no durable storage**. DeepSeek API usage may incur separate charges. Public role selection is not secure authentication.

## Tests and evidence

```powershell
.venv\Scripts\python.exe -m pytest tests -q
cd frontend
npm test
npm run lint
npm run build
```

The frozen integrated release was reported to pass **75 backend** and **23 frontend** tests; Terra also validated Docker locally with synthetic reservations and a mounted volume. These are historical/local results, not claims that the live Render Free instance persists data. See [QA report](docs/QA_REPORT.md) and [Docker validation](docs/DOCKER_VALIDATION.md). The Render Free deployment was reported Live; public endpoint, DeepSeek, camera and end-to-end acceptance must be checked separately.

## Documentation

- [System architecture](docs/ARCHITECTURE.md)
- [API contract](API_CONTRACT.md)
- [Feature traceability](docs/TRACEABILITY.md)
- [Quality assurance and gaps](docs/QA_REPORT.md)
- [Three-minute demo](docs/DEMO.md)
- [Render Free deployment and limitations](docs/RENDER_DEPLOY.md)
- [Local Docker validation](docs/DOCKER_VALIDATION.md)

## Team and acknowledgements

**QuantumByte**, ENEISOFT XVI 2026. Backend/integration: Leo; frontend/catalogue: Marco; local computer vision: David. Developed independently for an academic hackathon. No institutional affiliation or endorsement is implied.
