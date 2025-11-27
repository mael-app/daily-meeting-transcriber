FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

FROM python:3.11-slim-bookworm

WORKDIR /app

COPY --from=builder /usr/local /usr/local

COPY app.py .
COPY services/ services/
COPY utils/ utils/

EXPOSE 8080

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--workers=1", "--worker-class=uvicorn.workers.UvicornWorker", "--capture-output", "--log-level=info", "--timeout=120", "--graceful-timeout=120", "app:app"]
