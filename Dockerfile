FROM node:22-bookworm-slim@sha256:5ec23b7c622b00547753bc6ffd78085dd868a68aeb41c8e0a1418f033e13d96d AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54 AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CAMPUSTWIN_DB=/var/data/campustwin.db
WORKDIR /app
COPY requirements.txt requirements-render-lock.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c requirements-render-lock.txt && mkdir -p /var/data
COPY backend/ ./backend/
COPY --from=frontend-build /build/frontend/dist/ ./frontend/dist/
EXPOSE 10000
CMD ["sh", "-c", "exec python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
