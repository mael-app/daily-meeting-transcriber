FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos "" appuser

WORKDIR /app

COPY --from=builder /usr/local /usr/local

COPY app.py .
COPY services/ services/
COPY utils/ utils/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Timeout is set above Whisper's 600s limit to avoid premature worker kills.
# graceful-timeout allows in-flight requests to complete on shutdown.
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--workers=1", "--worker-class=uvicorn.workers.UvicornWorker", "--capture-output", "--log-level=info", "--timeout=650", "--graceful-timeout=30", "app:app"]
