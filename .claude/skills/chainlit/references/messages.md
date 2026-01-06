# Messages Reference

## Table of Contents
- [Overview](#overview)
- [Creating Messages](#creating-messages)
- [Message Properties](#message-properties)
- [Streaming](#streaming)
- [Chat Context](#chat-context)
- [Message with Elements](#message-with-elements)
- [Message with Actions](#message-with-actions)

## Overview

A Message represents information sent between user and assistant. Messages are the fundamental building blocks of chat applications and cannot be nested (use Steps for nested content).

## Creating Messages

### Basic Message

```python
import chainlit as cl

@cl.on_message
async def on_message(message: cl.Message):
    # Simple response
    await cl.Message(content="Hello!").send()
```

### With Author

```python
await cl.Message(
    content="I'm a custom assistant",
    author="CustomBot"
).send()
```

### Markdown Content

```python
await cl.Message(content="""
# Response

Here's some **bold** and *italic* text.

```python
print("Code block")
```

- List item 1
- List item 2
""").send()
```

## Message Properties

| Property | Type | Description |
|----------|------|-------------|
| `content` | str | Message text (supports markdown) |
| `author` | str | Display name (default: "Assistant") |
| `elements` | list | Attached UI elements |
| `actions` | list | Action buttons |
| `language` | str | Code language for syntax highlighting |

## Streaming

Stream tokens for real-time response display:

### Basic Streaming

```python
@cl.on_message
async def on_message(message: cl.Message):
    msg = cl.Message(content="")
    await msg.send()

    for token in ["Hello", " ", "world", "!"]:
        await msg.stream_token(token)
        await cl.sleep(0.1)  # Simulate delay

    await msg.update()
```

### OpenAI Streaming

```python
from openai import AsyncOpenAI

client = AsyncOpenAI()

@cl.on_message
async def on_message(message: cl.Message):
    msg = cl.Message(content="")
    await msg.send()

    stream = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": message.content}],
        stream=True
    )

    async for chunk in stream:
        if token := chunk.choices[0].delta.content:
            await msg.stream_token(token)

    await msg.update()
```

### Streaming with Steps

```python
@cl.on_message
async def on_message(message: cl.Message):
    # Show thinking step
    async with cl.Step(name="Thinking", type="llm") as step:
        step.input = message.content

        response = ""
        stream = await get_stream(message.content)
        async for token in stream:
            response += token
            await step.stream_token(token)

        step.output = response

    # Send final message
    await cl.Message(content=response).send()
```

## Chat Context

Automatic conversation history management:

### Get OpenAI Format

```python
@cl.on_message
async def on_message(message: cl.Message):
    # Get all messages in OpenAI format
    history = cl.chat_context.to_openai()
    # Returns: [{"role": "user", "content": "..."}, ...]

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=history
    )

    await cl.Message(content=response.choices[0].message.content).send()
```

### Add System Message

```python
@cl.on_chat_start
async def start():
    # System message is automatically included
    cl.user_session.set("system", "You are a helpful assistant.")

@cl.on_message
async def on_message(message: cl.Message):
    system = cl.user_session.get("system")
    history = cl.chat_context.to_openai()

    messages = [{"role": "system", "content": system}] + history

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )

    await cl.Message(content=response.choices[0].message.content).send()
```

## Message with Elements

Attach rich content to messages:

```python
@cl.on_message
async def on_message(message: cl.Message):
    # Text element
    text = cl.Text(
        name="analysis.txt",
        content="Detailed analysis results...",
        display="side"
    )

    # Image element
    image = cl.Image(
        name="chart.png",
        path="./chart.png",
        display="inline"
    )

    await cl.Message(
        content="Here are the results:",
        elements=[text, image]
    ).send()
```

## Message with Actions

Add interactive buttons:

```python
@cl.action_callback("thumbs_up")
async def on_thumbs_up(action: cl.Action):
    await cl.Message(content="Thanks for the feedback!").send()

@cl.action_callback("thumbs_down")
async def on_thumbs_down(action: cl.Action):
    await cl.Message(content="I'll try to improve.").send()

@cl.on_message
async def on_message(message: cl.Message):
    actions = [
        cl.Action(name="thumbs_up", label="👍", payload={"value": "positive"}),
        cl.Action(name="thumbs_down", label="👎", payload={"value": "negative"}),
    ]

    await cl.Message(
        content="How was this response?",
        actions=actions
    ).send()
```

## Update Existing Message

```python
@cl.on_message
async def on_message(message: cl.Message):
    msg = cl.Message(content="Processing...")
    await msg.send()

    # Do work...
    result = await process(message.content)

    # Update the message
    msg.content = f"Result: {result}"
    await msg.update()
```

## Remove Message

```python
@cl.on_message
async def on_message(message: cl.Message):
    loading = cl.Message(content="Loading...")
    await loading.send()

    result = await heavy_computation()

    # Remove loading message
    await loading.remove()

    # Send actual result
    await cl.Message(content=result).send()
```
