FROM node:20-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_URL=postgresql+asyncpg://wattsup:wattsup@postgres:5432/wattsup \
    FRONTEND_DIST=/app/frontend/dist
WORKDIR /app
RUN groupadd --system wattsup && useradd --system --gid wattsup --home-dir /app wattsup
COPY backend/pyproject.toml ./backend/
COPY backend/src ./backend/src
COPY backend/alembic.ini ./backend/
COPY backend/migrations ./backend/migrations
RUN pip install --no-cache-dir ./backend
COPY --from=frontend /build/frontend/dist ./frontend/dist
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint
RUN mkdir /data && chown wattsup:wattsup /data /app && chmod +x /usr/local/bin/docker-entrypoint
USER wattsup
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
ENTRYPOINT ["docker-entrypoint"]
