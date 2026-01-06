# Cloud and FastAPI Projects

A collection of FastAPI applications and AI-powered agents demonstrating modern Python development practices.

## Projects

### 1. Todo Agent (`todoAgent/`)

An AI-powered todo management agent with natural language interface.

**Features:**
- Natural language todo management (create, list, update, delete)
- Powered by Google Gemini with DeepSeek fallback
- **Chainlit Web UI** with streaming responses
- Tool call visualization

**Quick Start:**
```bash
cd todoAgent
uv sync
cp .env.example .env  # Add your API keys

# Start backend first (see todoApp below)
# Then run the Chainlit UI:
chainlit run chainlit_app.py -w --port 8005
```

Open http://localhost:8005 in your browser.

[Full Documentation](todoAgent/README.md)

---

### 2. Todo API (`todoApp/`)

FastAPI Todo REST API with SQLModel and async PostgreSQL (Neon).

**Features:**
- Full CRUD operations for todos
- Async PostgreSQL with SQLModel
- Pydantic validation
- Swagger/ReDoc documentation

**Quick Start:**
```bash
cd todoApp
uv sync
cp .env.example .env  # Add your database URL
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

API available at http://127.0.0.1:8080/docs

[Full Documentation](todoApp/README.md)

---

### 3. Hello World FastAPI (`hello-world-fastapi/`)

A simple FastAPI starter template.

```bash
cd hello-world-fastapi
pip install "fastapi[standard]"
fastapi dev main.py
```

[Full Documentation](hello-world-fastapi/README.md)

---

## Claude Code Skills (`.claude/skills/`)

This repository includes custom Claude Code skills for enhanced AI-assisted development:

| Skill | Description |
|-------|-------------|
| `chainlit` | Build conversational AI apps with Chainlit |
| `fastapi` | FastAPI REST API development |
| `openai-agents-sdk` | Multi-agent AI workflows |
| `pytest` | Python testing with pytest |
| `sqlmodel` | Database models with SQLModel |
| `context7-efficient` | Token-efficient documentation fetching |
| `browser-use` | Browser automation with Playwright |
| `pdf`, `docx`, `xlsx`, `pptx` | Document manipulation |

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐
│   Chainlit UI   │────▶│   Todo Agent    │
│  (Web Browser)  │     │ (OpenAI Agents) │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Todo API      │
                        │   (FastAPI)     │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   PostgreSQL    │
                        │     (Neon)      │
                        └─────────────────┘
```

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- API Keys:
  - Google Gemini API key (for Todo Agent)
  - PostgreSQL database URL (for Todo API)

## Quick Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Salmanferozkhan/Cloud-and-fast-api.git
   cd Cloud-and-fast-api
   ```

2. Start the Todo API backend:
   ```bash
   cd todoApp
   uv sync
   cp .env.example .env  # Configure DATABASE_URL
   uv run uvicorn main:app --reload --port 8080
   ```

3. In a new terminal, start the Todo Agent:
   ```bash
   cd todoAgent
   uv sync
   cp .env.example .env  # Add GEMINI_API_KEY
   chainlit run chainlit_app.py -w --port 8005
   ```

4. Open http://localhost:8005 and start managing todos with natural language!

## License

MIT
