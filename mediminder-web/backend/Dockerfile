# Multi-stage build. Uses python:3.13-slim rather than 3.14-slim because
# pydantic-core / asyncpg still lack cp314 wheels as of the build date, and
# compiling PyO3 from source inside a slim image is fragile (PyO3 currently
# tops out at Python 3.13). See docs/DECISIONS.md#d-19.
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Minimal build deps — mostly a safety net in case any dep temporarily lacks
# a wheel. libpq-dev is the source-build fallback for psycopg-family libs.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install -r requirements.txt

# --- runtime image -----------------------------------------------------------
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:${PATH}" \
    PYTHONPATH="/app:/install/lib/python3.13/site-packages"

# Only the shared libs we need at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1001 appuser

WORKDIR /app
COPY --from=builder /install /install
COPY app ./app

USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
