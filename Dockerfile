FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY . .

COPY entrypoint_k8s.sh /entrypoint_k8s.sh
RUN chmod +x /entrypoint_k8s.sh

RUN useradd -m appuser && chown -R appuser /app
USER appuser

ENTRYPOINT ["/entrypoint_k8s.sh"]

CMD ["gunicorn", "-w", "4", "--bind", "0.0.0.0:5000", "wsgi:app"]