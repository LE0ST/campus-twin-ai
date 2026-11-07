# Render Free — CampusTwin AI

## Verified service metadata (7 November 2026)

- Public URL: https://campustwin-ai-demo.onrender.com
- Render service: `srv-dbnp5q49v7es73dcp1jg`
- Service name: `campustwin-ai-demo`
- Plan: **Free**, Ohio, Docker, one instance, automatic deploy **off**
- First successfully Live deployment: `b350ff550c954138ea05baaeae1beae93557658c`
- Repository's intended canonical branch: `main`. **Changing the repository branch does not automatically switch the existing Render service branch**; verify it in Render dashboard before claiming the deployed SHA is from `main`.
- A successful build or Live status does not substitute for HTTP/visual smoke tests.

## Deployment design

Docker multi-stage Node build + Python runtime serves React/Vite and FastAPI on one origin. `PORT` is supplied by Render. Backend SQLite database is `/tmp/campustwin-demo.db` via `CAMPUSTWIN_DB`.

**No persistent disk is attached.** Data may be lost when Render Free suspends, restarts, redeploys or replaces an instance. Never claim persistent reservations or backup/recovery. A cold start may take time. Render Free limits apply.

`render.yaml` describes the intended configuration but is **not** proof of a Blueprint deployment. Do not apply it to create a duplicate service. The existing service was created directly.

## Secrets and external dependencies

Configure only on Render's Environment screen:
- `DEEPSEEK_API_KEY`: optional assistant API secret; separate provider costs may apply.
- `DEEPSEEK_MODEL`: configured model ID.
- `VISION_INGEST_TOKEN`: same secret as the external authorized vision sender.
- `CAMPUSTWIN_DB=/tmp/campustwin-demo.db`.

Changing environment variables can restart or redeploy the service, resetting SQLite. Do not expose or log values.

## Vision integration

YOLO11n and camera run on a separate Windows computer. The client posts numeric counts to `POST /api/telemetry` with Bearer token. No camera hardware or inference runs on Render. The client must target the public URL and show `202 Accepted`; check Render logs and the room `R01` display. Missing or stale readings are **unknown**.

## Acceptance checklist

1. Verify Render branch, commit, plan and Live status.
2. GET `/api/health` -> 200.
3. GET `/` -> HTML and assets load in browser.
4. GET `/api/rooms` -> 200 with valid date/slot.
5. Test fictional reservation, duplicate request and conflict; never use real data.
6. Confirm optional assistant separately with authorized credentials.
7. Confirm camera separately by receiving HTTP 202 and observing the R01 count.
8. Explain ephemeral SQLite and public demo roles to evaluators.

## Paid persistent alternative (NOT deployed)

Terra validated a separate local Docker configuration with a mounted volume and proposed Starter + 1 GB disk, roughly USD 7.25/month before taxes and variable charges. **No paid deployment was authorized or created.** Its Docker validation evidence remains in [DOCKER_VALIDATION.md](DOCKER_VALIDATION.md). Do not apply a paid Blueprint without explicit cost approval.
