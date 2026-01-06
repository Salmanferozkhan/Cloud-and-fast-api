# User Session Reference

## Table of Contents
- [Overview](#overview)
- [Basic Operations](#basic-operations)
- [Reserved Keys](#reserved-keys)
- [Common Patterns](#common-patterns)
- [Session vs Global State](#session-vs-global-state)

## Overview

The user session persists data in memory through a chat session's lifecycle. Each session is isolated per user, preventing data conflicts when multiple users interact simultaneously.

## Basic Operations

### Set Value

```python
import chainlit as cl

@cl.on_chat_start
async def start():
    # Store values
    cl.user_session.set("counter", 0)
    cl.user_session.set("messages", [])
    cl.user_session.set("config", {"model": "gpt-4", "temperature": 0.7})
```

### Get Value

```python
@cl.on_message
async def on_message(message: cl.Message):
    # Retrieve values
    counter = cl.user_session.get("counter")
    messages = cl.user_session.get("messages")
    config = cl.user_session.get("config")

    # With default value
    name = cl.user_session.get("name", "Anonymous")
```

### Update Value

```python
@cl.on_message
async def on_message(message: cl.Message):
    # Get, modify, set
    counter = cl.user_session.get("counter", 0)
    counter += 1
    cl.user_session.set("counter", counter)

    # Lists and dicts
    messages = cl.user_session.get("messages", [])
    messages.append({"role": "user", "content": message.content})
    cl.user_session.set("messages", messages)
```

## Reserved Keys

Chainlit automatically stores these values:

| Key | Type | Description |
|-----|------|-------------|
| `id` | str | Session identifier |
| `user` | User | Authenticated user (if auth enabled) |
| `chat_profile` | str | Selected chat profile name |
| `chat_settings` | dict | User-provided settings |
| `env` | dict | Environment variables |

### Access Reserved Keys

```python
@cl.on_chat_start
async def start():
    # Session ID
    session_id = cl.user_session.get("id")

    # Authenticated user (if auth enabled)
    user = cl.user_session.get("user")
    if user:
        await cl.Message(content=f"Hello, {user.identifier}!").send()

    # Chat profile
    profile = cl.user_session.get("chat_profile")

    # Chat settings
    settings = cl.user_session.get("chat_settings")
```

## Common Patterns

### Store LLM Client

```python
from openai import AsyncOpenAI

@cl.on_chat_start
async def start():
    client = AsyncOpenAI()
    cl.user_session.set("client", client)

@cl.on_message
async def on_message(message: cl.Message):
    client = cl.user_session.get("client")
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": message.content}]
    )
    await cl.Message(content=response.choices[0].message.content).send()
```

### Conversation History

```python
@cl.on_chat_start
async def start():
    cl.user_session.set("history", [
        {"role": "system", "content": "You are a helpful assistant."}
    ])

@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history")
    history.append({"role": "user", "content": message.content})

    client = cl.user_session.get("client")
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=history
    )

    assistant_message = response.choices[0].message.content
    history.append({"role": "assistant", "content": assistant_message})
    cl.user_session.set("history", history)

    await cl.Message(content=assistant_message).send()
```

### User Preferences

```python
@cl.on_chat_start
async def start():
    # Set defaults
    cl.user_session.set("preferences", {
        "language": "en",
        "verbosity": "normal",
        "format": "markdown"
    })

@cl.on_message
async def on_message(message: cl.Message):
    prefs = cl.user_session.get("preferences")

    # Check for preference commands
    if message.content.startswith("/set"):
        parts = message.content.split()
        if len(parts) == 3:
            key, value = parts[1], parts[2]
            prefs[key] = value
            cl.user_session.set("preferences", prefs)
            await cl.Message(content=f"Set {key} to {value}").send()
            return

    # Use preferences in response generation
    response = await generate_response(message.content, prefs)
    await cl.Message(content=response).send()
```

### Store Complex Objects

```python
from dataclasses import dataclass
from typing import List

@dataclass
class Document:
    id: str
    content: str
    embeddings: List[float]

@cl.on_chat_start
async def start():
    # Load and store documents
    docs = await load_documents()
    cl.user_session.set("documents", docs)

    # Store index
    index = create_index(docs)
    cl.user_session.set("index", index)

@cl.on_message
async def on_message(message: cl.Message):
    index = cl.user_session.get("index")
    docs = cl.user_session.get("documents")

    # Search documents
    results = search(index, message.content)
    relevant_docs = [docs[i] for i in results]

    await cl.Message(content=format_results(relevant_docs)).send()
```

## Session vs Global State

### Wrong: Global Variables

```python
# DON'T DO THIS - shared across all users!
counter = 0
messages = []

@cl.on_message
async def on_message(message: cl.Message):
    global counter, messages
    counter += 1  # All users share this!
    messages.append(message.content)  # Mixed messages from all users!
```

### Correct: User Session

```python
@cl.on_chat_start
async def start():
    cl.user_session.set("counter", 0)
    cl.user_session.set("messages", [])

@cl.on_message
async def on_message(message: cl.Message):
    # Each user has their own counter and messages
    counter = cl.user_session.get("counter")
    counter += 1
    cl.user_session.set("counter", counter)

    messages = cl.user_session.get("messages")
    messages.append(message.content)
    cl.user_session.set("messages", messages)
```

### When Global State is OK

```python
# Shared read-only resources are fine
MODEL = load_model()  # Load once, share across users
CONFIG = load_config()  # Immutable configuration

@cl.on_chat_start
async def start():
    # Each user gets their own session state
    cl.user_session.set("model", MODEL)  # Reference to shared model
    cl.user_session.set("user_config", CONFIG.copy())  # Copy for user-specific changes
```

## Cleanup

Session data is automatically cleared when the chat ends. For manual cleanup:

```python
@cl.on_chat_end
async def end():
    # Explicit cleanup of resources
    client = cl.user_session.get("client")
    if client:
        await client.close()

    # Clear sensitive data
    cl.user_session.set("api_key", None)
```
