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

# Default uvicorn launch (overridable by platform PORT env)
ENV PORT=8000
EXPOSE 8000

# Run from src/ so `app.main:app` resolves
WORKDIR /app/src
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]