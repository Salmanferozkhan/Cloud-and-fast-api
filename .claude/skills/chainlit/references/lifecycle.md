# Chat Lifecycle Reference

## Table of Contents
- [Overview](#overview)
- [on_chat_start](#on_chat_start)
- [on_message](#on_message)
- [on_chat_end](#on_chat_end)
- [on_chat_resume](#on_chat_resume)
- [on_stop](#on_stop)
- [Complete Example](#complete-example)

## Overview

When a user connects to your Chainlit app, a new chat session is created. The session goes through lifecycle events you can respond to with hooks.

## on_chat_start

Executes when a new chat session begins. Use for initialization:

```python
import chainlit as cl

@cl.on_chat_start
async def on_chat_start():
    # Initialize session variables
    cl.user_session.set("history", [])

    # Load models or resources
    model = load_model()
    cl.user_session.set("model", model)

    # Send welcome message
    await cl.Message(content="Welcome! How can I help you?").send()
```

### Common Use Cases

```python
@cl.on_chat_start
async def start():
    # Store LLM client
    from openai import AsyncOpenAI
    client = AsyncOpenAI()
    cl.user_session.set("client", client)

    # Initialize conversation history
    cl.user_session.set("messages", [
        {"role": "system", "content": "You are a helpful assistant."}
    ])
```

## on_message

Responds to user messages. Receives the message object:

```python
@cl.on_message
async def on_message(message: cl.Message):
    # Access message content
    user_input = message.content

    # Process and respond
    response = await process(user_input)
    await cl.Message(content=response).send()
```

### With Conversation History

```python
@cl.on_message
async def on_message(message: cl.Message):
    # Get stored history
    messages = cl.user_session.get("messages")
    messages.append({"role": "user", "content": message.content})

    # Get response from LLM
    client = cl.user_session.get("client")
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )

    assistant_message = response.choices[0].message.content
    messages.append({"role": "assistant", "content": assistant_message})

    # Update history and respond
    cl.user_session.set("messages", messages)
    await cl.Message(content=assistant_message).send()
```

### Using chat_context

```python
@cl.on_message
async def on_message(message: cl.Message):
    # Automatic conversation history in OpenAI format
    history = cl.chat_context.to_openai()

    client = cl.user_session.get("client")
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=history
    )

    await cl.Message(content=response.choices[0].message.content).send()
```

## on_chat_end

Triggers when session ends (disconnect or new chat):

```python
@cl.on_chat_end
async def on_chat_end():
    # Cleanup resources
    model = cl.user_session.get("model")
    if model:
        model.cleanup()

    # Log session end
    print("Chat session ended")
```

### Save Conversation

```python
@cl.on_chat_end
async def on_chat_end():
    # Save conversation history
    history = cl.user_session.get("messages")
    user = cl.user_session.get("user")

    if history and user:
        await save_conversation(user.identifier, history)
```

## on_chat_resume

Activates when users reconnect to previous sessions. Requires authentication and data persistence:

```python
from chainlit.types import ThreadDict

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    # Restore session state
    print(f"Resumed thread: {thread['id']}")

    # Rebuild conversation history from thread
    messages = []
    for step in thread["steps"]:
        if step["type"] == "user_message":
            messages.append({"role": "user", "content": step["output"]})
        elif step["type"] == "assistant_message":
            messages.append({"role": "assistant", "content": step["output"]})

    cl.user_session.set("messages", messages)

    await cl.Message(content="Welcome back! Continuing our conversation...").send()
```

## on_stop

Responds to user clicking stop button during execution:

```python
@cl.on_stop
async def on_stop():
    # Handle interruption
    print("User stopped the current task")

    # Cleanup any running operations
    task = cl.user_session.get("current_task")
    if task:
        task.cancel()
```

## Complete Example

Full chatbot with all lifecycle hooks:

```python
import chainlit as cl
from openai import AsyncOpenAI

client = AsyncOpenAI()

@cl.on_chat_start
async def on_chat_start():
    # Initialize session
    cl.user_session.set("messages", [
        {"role": "system", "content": "You are a helpful assistant."}
    ])

    await cl.Message(content="Hello! How can I assist you today?").send()

@cl.on_message
async def on_message(message: cl.Message):
    messages = cl.user_session.get("messages")
    messages.append({"role": "user", "content": message.content})

    # Stream response
    msg = cl.Message(content="")
    await msg.send()

    stream = await client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        stream=True
    )

    full_response = ""
    async for chunk in stream:
        if token := chunk.choices[0].delta.content:
            full_response += token
            await msg.stream_token(token)

    await msg.update()

    messages.append({"role": "assistant", "content": full_response})
    cl.user_session.set("messages", messages)

@cl.on_chat_end
async def on_chat_end():
    print("Session ended")

@cl.on_stop
async def on_stop():
    print("User interrupted")
```
