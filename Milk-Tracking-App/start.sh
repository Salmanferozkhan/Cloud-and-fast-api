#!/bin/bash
set -e

cd /app/api
python -m uvicorn main:app --host 127.0.0.1 --port 8076 &

for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8076/health > /dev/null; then
        echo "[start.sh] API ready."
        break
    fi
    echo "[start.sh] waiting for API ($i/30)..."
    sleep 1
done

cd /app/agent
# Chainlit auto-enables a SQL data layer when DATABASE_URL is set, but it
# expects its own Thread/Step tables. Our Neon DB is for the API only —
# unset so chainlit falls back to in-memory (chat history not persisted).
unset DATABASE_URL
exec chainlit run chainlit_app.py --host 0.0.0.0 --port "${PORT:-7860}" --headless
