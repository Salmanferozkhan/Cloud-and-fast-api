#!/bin/bash
set -e

cd /app/api
python -m uvicorn main:app --host 127.0.0.1 --port 8076 &
API_PID=$!

# Neon (and most managed Postgres) can take 10-30s to wake from idle on the
# first connection, so allow a generous budget before falling through.
for i in $(seq 1 90); do
    if curl -sf http://127.0.0.1:8076/health > /dev/null; then
        echo "[start.sh] API ready after ${i}s."
        break
    fi
    if ! kill -0 "$API_PID" 2>/dev/null; then
        echo "[start.sh] API process exited — check uvicorn traceback above."
        break
    fi
    echo "[start.sh] waiting for API ($i/90)..."
    sleep 1
done

if ! curl -sf http://127.0.0.1:8076/health > /dev/null; then
    echo "[start.sh] WARNING: API not reachable; chainlit will start but tool calls will fail."
fi

cd /app/agent
# Chainlit auto-enables a SQL data layer when DATABASE_URL is set, but it
# expects its own Thread/Step tables. Our Neon DB is for the API only —
# unset so chainlit falls back to in-memory (chat history not persisted).
unset DATABASE_URL
exec chainlit run chainlit_app.py --host 0.0.0.0 --port "${PORT:-7860}" --headless
