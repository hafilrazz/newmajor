FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONPATH=/app

WORKDIR /app

# System libs used by Pillow / scientific stack
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgl1 \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

# Application code (Flask UI templates/static + API + ML services)
COPY backend /app/backend
COPY models /app/models

# Runtime defaults for the unified Flask app (HTML UI + JSON API)
ENV FLASK_PORT=5000
ENV FLASK_DEBUG=0
ENV FLASK_USE_RELOADER=0
ENV FLASK_SECRET_KEY=neurolens-docker-change-me
ENV MODEL_PATH=/app/models/model.pth
ENV MONGODB_URI=mongodb://mongo:27017
ENV MONGODB_DB=alzheimers
ENV CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000

# Writable cache for session UI blobs (MRI / Grad-CAM previews)
RUN mkdir -p /app/data/ui_cache

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD curl -fsS http://127.0.0.1:5000/health >/dev/null || exit 1

# Single worker recommended while model is loaded in-process
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "1", \
     "--threads", "2", \
     "--timeout", "180", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "backend.wsgi:app"]
