# NeuroLens — Clinical Multi-Modal Intelligence Platform
# Convenience Root Dockerfile (equivalent to backend/Dockerfile)
#
# Build:
#   docker build -t neurolens-web .
# Run:
#   docker run -p 5000:5000 neurolens-web

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
    CT_MODEL_PATH=/app/models/ct_stacking_ensemble.pth \
    CLINICAL_MODEL_PATH=/app/models/randomforest_clinical.joblib \
    CLINICAL_XGB_PATH=/app/models/xgboost_clinical.json \
    MONGODB_URI=mongodb://mongo:27017 \
    MONGODB_DB=alzheimers \
    CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000

WORKDIR /app

# Install system dependencies:
# - curl: healthcheck endpoint polling
# - ca-certificates: secure HTTPS asset retrieval
# - libglib2.0-0, libgl1: image manipulation libraries
# - libgomp1: OpenMP runtime (required for PyTorch and XGBoost)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        libglib2.0-0 \
        libgl1 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for optimal Docker layer caching
COPY backend/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --extra-index-url https://download.pytorch.org/whl/cpu -r /app/requirements.txt

# Copy application source code
COPY backend /app/backend

# Copy all trained model weights (MRI ResNet-18, CT MobileNetV2/EfficientNet-B0/Stacking, Clinical RF/XGBoost)
COPY models /app/models

# Create writable data directories for isolated UI cache and offline storage
RUN mkdir -p /app/data/ui_cache /app/data

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=8s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:5000/health >/dev/null || exit 1

# Production WSGI server (Gunicorn) with multithreading
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "1", \
     "--threads", "4", \
     "--timeout", "180", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "backend.wsgi:app"]
