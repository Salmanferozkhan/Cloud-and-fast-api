FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN useradd -m -u 1000 user

WORKDIR /app

COPY --chown=user:user requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY --chown=user:user api/ /app/api/
COPY --chown=user:user agent/ /app/agent/
COPY --chown=user:user start.sh /app/start.sh

RUN chmod +x /app/start.sh && \
    mkdir -p /app/agent/.files /app/agent/.chainlit && \
    chown -R user:user /app

USER user

ENV API_BASE_URL=http://localhost:8076 \
    PORT=7860

EXPOSE 7860

CMD ["/app/start.sh"]
