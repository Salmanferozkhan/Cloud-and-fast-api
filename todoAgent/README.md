# Todo Agent

An AI-powered todo management agent built with OpenAI Agents SDK and Google Gemini, with automatic fallback to DeepSeek API.

## Features

- List, create, update, and delete todos via natural language
- Mark todos as complete/incomplete
- Connects to your existing Todo FastAPI backend
- Powered by Google Gemini with DeepSeek fallback
- Automatic API fallback when Gemini quota is exhausted

## Prerequisites

1. **Todo FastAPI server** running at `http://127.0.0.1:8080`
2. **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/apikey)
3. **DeepSeek API Key** (optional, for fallback) from [DeepSeek](https://platform.deepseek.com/)

## Setup

1. Install dependencies using uv:
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   pip install -e .
   ```

2. Create `.env` file:
   ```bash
   cp .env.example .env
   ```

3. Add your API keys to `.env`:
   ```
   GEMINI_API_KEY=your-gemini-api-key-here
   DEEPSEEK_API_KEY=your-deepseek-api-key-here  # Optional fallback
   ```

## Running the Application

### Option A: Chainlit Web UI (Recommended)

1. Start the Todo Backend Server (see Step 1 below)
2. Run the Chainlit UI:
   ```bash
   chainlit run chainlit_app.py -w --port 8005
   ```
3. Open http://localhost:8005 in your browser

Features:
- Streaming responses (text appears token by token)
- Tool call visualization (see each API call as expandable steps)
- Conversation history

### Option B: Command Line Interface

### Step 1: Start the Todo Backend Server

Navigate to the todoApp directory and start the FastAPI server:

```bash
cd ../todoApp
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

Or without uv:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

The backend API will be available at:
- API: `http://127.0.0.1:8080`
- Docs: `http://127.0.0.1:8080/docs`
- Health: `http://127.0.0.1:8080/health`

### Step 2: Run the Todo Agent

In a new terminal, navigate to the todoAgent directory and run:

```bash
uv run main.py
```

Or without uv:
```bash
python main.py
```

### Step 3: Interact with Natural Language

```
You: Show me my todos
You: Create a todo to buy groceries
You: Mark todo 1 as complete
You: Delete todo 2
```

## Project Structure

```
todoAgent/
├── main.py           # CLI entry point with chat loop
├── chainlit_app.py   # Chainlit Web UI with streaming
├── agent.py          # Agent configuration with Gemini + DeepSeek fallback
├── tools.py          # API client tools for todo operations
├── pyproject.toml    # Dependencies
├── .env.example      # Environment template
└── README.md         # This file
```

## API Fallback

The agent automatically falls back to DeepSeek API when:
- Gemini API returns rate limit errors (HTTP 429)
- Gemini quota is exhausted
- Service unavailable errors (HTTP 503)

You'll see a message like:
```
[Fallback] Gemini API exhausted, switching to DeepSeek
```

## Example Interactions

```
You: What are my current tasks?
Agent: Here are your current todos:
- [1] Buy groceries (pending)
- [2] Finish report - Due Friday (completed)

You: Add a todo to call mom
Agent: Created todo #3: 'Call mom'

You: Mark task 1 as done
Agent: Marked todo #1 'Buy groceries' as completed!
```
