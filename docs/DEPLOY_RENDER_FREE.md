# Render Free — CampusTwin AI demo

This deployment is a public **academic prototype with fictitious room and reservation data**, not a UNMSM institutional system.

- Branch: `deploy/render-free-2026-11-07`, derived from frozen release candidate `f004ac30af709b6f9335d057700f23d3191cd768`.
- One Docker web service serves React/Vite static build and FastAPI under the same origin.
- Build: multi-stage Node 22 + Python 3.12; Uvicorn uses `$PORT`, one worker.
- Health: `GET /api/health`; rooms: `GET /api/rooms`.
- SQLite: `CAMPUSTWIN_DB=/tmp/campustwin-demo.db`. **Ephemeral**. Reservations may be lost on suspend, restart, redeploy, or instance replacement. No backups, durable data, authentication, or institutional records.
- Telemetry: absent by default. Without `VISION_INGEST_TOKEN`, authenticated ingestion is unavailable and occupancy should be unknown. No camera or YOLO process is hosted.
- DeepSeek: without `DEEPSEEK_API_KEY`, assistant requests can return 503 and users must use the manual form. A key must only be configured as a secret environment variable in Render; enabling it may incur API charges.
- Render Free may sleep after inactivity, incur cold starts, and is subject to workspace usage quotas.
- No real personal data should be entered. Profiles are UI demonstrations without access controls.

## Smoke test after deployment

1. Verify service's deployed commit and status in Render.
2. `GET https://<render-host>/api/health` -> 200 JSON.
3. `GET https://<render-host>/` -> 200 HTML with React assets.
4. `GET https://<render-host>/api/rooms?date=<today-Lima>&slot_id=S18` -> 200 if the date and slot are allowed.
5. Check UI loads and can navigate to Secretary. If testing reservation, use only fictional data and a future valid slot; expect 201 then same request_id 200 and conflicting request_id 409.
6. Document that data can disappear after suspend/restart. Never call the deployment persistent.

Do not enable automatic deploys or merge the infrastructure branch to main until approved.
