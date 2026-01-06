# Sessions Reference

## Table of Contents
- [Overview](#overview)
- [SQLite Sessions](#sqlite-sessions)
- [OpenAI Conversations API](#openai-conversations-api)
- [SQLAlchemy Sessions](#sqlalchemy-sessions)
- [Encrypted Sessions](#encrypted-sessions)
- [Memory Operations](#memory-operations)
- [Multi-Agent Sessions](#multi-agent-sessions)

## Overview

Sessions automatically maintain conversation history across multiple agent runs. The system:

1. Retrieves history before each run
2. Prepends history to new inputs
3. Stores new items after completion
4. Enables stateful multi-turn conversations

## SQLite Sessions

Lightweight option for local persistence:

```python
from agents import Agent, Runner
from agents.extensions.session import SQLiteSession

# In-memory session (lost on restart)
session = SQLiteSession("user_123")

# File-based persistence
session = SQLiteSession("user_123", "conversations.db")

agent = Agent(name="Assistant", instructions="Be helpful")

# First turn
result = await Runner.run(agent, "My name is Alice", session=session)

# Second turn (remembers the name)
result = await Runner.run(agent, "What's my name?", session=session)
# Output: "Your name is Alice"
```

## OpenAI Conversations API

Cloud-hosted session management:

```python
from agents.extensions.session import OpenAIConversationsSession

# Uses OpenAI's infrastructure
session = OpenAIConversationsSession()

agent = Agent(name="Assistant", instructions="Be helpful")

# Conversations are stored on OpenAI's servers
result = await Runner.run(agent, "Remember this: secret123", session=session)
```

## SQLAlchemy Sessions

Production-ready with any SQL database:

```python
from sqlalchemy import create_engine
from agents.extensions.session import SQLAlchemySession

# PostgreSQL
engine = create_engine("postgresql://user:pass@localhost/db")
session = SQLAlchemySession("user_123", engine)

# MySQL
engine = create_engine("mysql://user:pass@localhost/db")
session = SQLAlchemySession("user_123", engine)

# With connection pool
engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_size=10,
    max_overflow=20,
)
session = SQLAlchemySession("user_123", engine)
```

## Encrypted Sessions

Add encryption to any session type:

```python
from agents.extensions.session import SQLiteSession, EncryptedSession

# Base session
base_session = SQLiteSession("user_123", "conversations.db")

# Wrap with encryption
session = EncryptedSession(
    base_session,
    encryption_key="your-32-byte-encryption-key-here",
    ttl=3600,  # Optional: expire after 1 hour
)

# Use normally - encryption is transparent
result = await Runner.run(agent, "Sensitive data", session=session)
```

## Memory Operations

### Get Conversation History

```python
session = SQLiteSession("user_123")

# Retrieve all items
history = await session.get_items()
for item in history:
    print(f"{item.type}: {item.content}")
```

### Add Items Manually

```python
from agents.items import MessageInputItem

# Add a system message
await session.add_items([
    MessageInputItem(role="system", content="User prefers formal language")
])
```

### Remove Last Item

```python
# Undo last interaction
removed = await session.pop_item()
print(f"Removed: {removed}")
```

### Clear Session

```python
# Reset conversation
await session.clear_session()
```

## Multi-Agent Sessions

Share sessions across agents:

```python
from agents import Agent, Runner
from agents.extensions.session import SQLiteSession

# Shared session
session = SQLiteSession("support_ticket_456")

# Different agents, same conversation
triage = Agent(name="Triage", instructions="Route customers")
billing = Agent(name="Billing", instructions="Handle billing")
technical = Agent(name="Technical", instructions="Solve tech issues")

# Triage first
result = await Runner.run(
    triage,
    "I have a billing question",
    session=session,
)

# Handoff to billing (same session maintains context)
result = await Runner.run(
    billing,
    "Can you help with my invoice?",
    session=session,
)
```

## Session ID Best Practices

Use meaningful, unique identifiers:

```python
# Per-user sessions
session = SQLiteSession(f"user_{user_id}")

# Per-conversation threads
session = SQLiteSession(f"thread_{thread_id}")

# Support tickets
session = SQLiteSession(f"ticket_{ticket_number}")

# Composite IDs
session = SQLiteSession(f"user_{user_id}_conv_{conversation_id}")
```

## Complete Example

Multi-turn chatbot with persistence:

```python
from agents import Agent, Runner
from agents.extensions.session import SQLiteSession

class ChatBot:
    def __init__(self, db_path: str = "chats.db"):
        self.db_path = db_path
        self.agent = Agent(
            name="ChatBot",
            instructions="""You are a friendly assistant.
            Remember details users share and reference them naturally.""",
        )

    async def chat(self, user_id: str, message: str) -> str:
        session = SQLiteSession(user_id, self.db_path)
        result = await Runner.run(self.agent, message, session=session)
        return result.final_output

    async def clear_history(self, user_id: str):
        session = SQLiteSession(user_id, self.db_path)
        await session.clear_session()

# Usage
bot = ChatBot()

# Conversation persists across calls
response1 = await bot.chat("alice", "I love hiking in Colorado")
response2 = await bot.chat("alice", "What outdoor activities would you recommend?")
# Bot remembers Alice likes hiking in Colorado
```
