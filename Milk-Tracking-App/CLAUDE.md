# Claude Instructions for Milk Tracking App

## Run the Project

When user says "run the project" or "start the servers", execute these two commands in background:

### 1. Start FastAPI Backend (Port 8076)
```bash
cd F:/GenAI/cloud/Milk-Tracking-App/api && uv run uvicorn main:app --reload --port 8076
```

### 2. Start Chainlit Agent UI (Port 8005)
```bash
cd F:/GenAI/cloud/Milk-Tracking-App/agent && uv run chainlit run chainlit_app.py -w --port 8005
```

## URLs
- API Swagger: http://localhost:8076/docs
- Chainlit Chat: http://localhost:8005

## Test the API
```bash
cd F:/GenAI/cloud/Milk-Tracking-App/api && uv run pytest -v
```

## Register a User (Required First Time)
```bash
curl -X POST http://localhost:8076/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```
