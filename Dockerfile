# QueueStorm Warmup — production container
# CPU-only, no GPU, ~30 MB installed dependencies.

FROM python:3.12-slim AS base

# Avoid writing .pyc files and force stdout flush (important for log streaming)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Install deps first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code into /app/src so the `app` package lives at /app/src/app/
COPY src/ ./src/

# Railway / Render / Cloud Run inject $PORT; default to 8000 for plain `docker run`.
# Use a shell-form CMD so the ${PORT:-8000} expansion happens at runtime.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]