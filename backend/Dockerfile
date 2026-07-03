# Slim, current base image to minimize vulnerabilities.
FROM python:3.14-slim

# Avoid .pyc and buffer issues; predictable logging.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code + synthetic seed data.
COPY app ./app
COPY seed_data ./seed_data

# Run as a non-root user.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Cloud Run injects $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
