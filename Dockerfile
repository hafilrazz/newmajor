# Convenience root Dockerfile — same image as backend/Dockerfile
# Build: docker build -t neurolens-web .
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    FLASK_PORT=5000 \
    FLASK_DEBUG=0 \
    FLASK_USE_RELOADER=0 \
    FLASK_SECRET_KEY=neurolens-docker-change-me \
    MODEL_PATH=/app/models/model.pth \
    MONGODB_URI=mongodb://mongo:27017 \
    MONGODB_DB=alzheimers \
    CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        libglib2.0-0 \
        libgl1 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install -r /app/requirements.txt

COPY backend /app/backend
COPY models /app/models

RUN mkdir -p /app/data/ui_cache /app/data

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=8s --start-period=120s --retries=3 \
    CMD curl -fsS http://127.0.0.1:5000/health >/dev/null || exit 1

CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "1", \
     "--threads", "2", \
     "--timeout", "180", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "backend.wsgi:app"]
