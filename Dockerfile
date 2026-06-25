# QueueStorm Warmup — production container
# CPU-only, no GPU, ~30 MB installed dependencies.

FROM python:3.12-slim AS base

# Avoid writing .pyc files and force stdout flush (important for log streaming)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install deps first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Railway / Render / Cloud Run inject $PORT; default to 8000 for plain `docker run`.
WORKDIR /app/src
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]