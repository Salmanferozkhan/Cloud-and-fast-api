# Ask User Reference

## Table of Contents
- [Overview](#overview)
- [AskUserMessage](#askusermessage)
- [AskFileMessage](#askfilemessage)
- [AskActionMessage](#askactionmessage)
- [Timeout Handling](#timeout-handling)
- [Common Patterns](#common-patterns)

## Overview

Ask User APIs block execution until user input is received. The UI prevents further chat interaction until the user responds. All ask functions are async and return `None` if timeout is reached.

## AskUserMessage

Prompt user for text input:

### Basic Usage

```python
import chainlit as cl

@cl.on_chat_start
async def start():
    response = await cl.AskUserMessage(
        content="What is your name?",
        timeout=60
    ).send()

    if response:
        name = response.get("output")
        await cl.Message(content=f"Hello, {name}!").send()
    else:
        await cl.Message(content="No response received.").send()
```

### Multi-Step Form

```python
@cl.on_chat_start
async def start():
    # Ask for name
    name_response = await cl.AskUserMessage(
        content="What is your name?",
        timeout=120
    ).send()

    if not name_response:
        return

    name = name_response.get("output")

    # Ask for email
    email_response = await cl.AskUserMessage(
        content=f"Hi {name}! What's your email?",
        timeout=120
    ).send()

    if not email_response:
        return

    email = email_response.get("output")

    # Store user info
    cl.user_session.set("user_info", {"name": name, "email": email})

    await cl.Message(content="Thanks! You're all set.").send()
```

## AskFileMessage

Request file uploads:

### Single File

```python
@cl.on_chat_start
async def start():
    files = await cl.AskFileMessage(
        content="Please upload a text file",
        accept=["text/plain"],
        max_size_mb=10,
        timeout=180
    ).send()

    if files:
        file = files[0]
        content = file.content.decode("utf-8")
        await cl.Message(content=f"File content:\n{content}").send()
```

### Multiple Files

```python
@cl.on_chat_start
async def start():
    files = await cl.AskFileMessage(
        content="Upload your images (up to 5)",
        accept=["image/png", "image/jpeg"],
        max_files=5,
        max_size_mb=20,
        timeout=180
    ).send()

    if files:
        await cl.Message(content=f"Received {len(files)} files").send()

        for file in files:
            # Process each file
            image = cl.Image(
                name=file.name,
                content=file.content,
                display="inline"
            )
            await cl.Message(
                content=f"Uploaded: {file.name}",
                elements=[image]
            ).send()
```

### Accept Types

```python
# Documents
accept=["application/pdf", "text/plain", "application/msword"]

# Images
accept=["image/*"]  # All images
accept=["image/png", "image/jpeg"]  # Specific types

# Data files
accept=[".csv", ".json", ".xlsx"]

# Any file
accept=["*/*"]
```

### File Properties

```python
files = await cl.AskFileMessage(content="Upload file").send()

if files:
    file = files[0]

    # Available properties
    name = file.name          # Filename
    content = file.content    # Bytes content
    type = file.type          # MIME type
    size = file.size          # Size in bytes
    path = file.path          # Temporary file path
```

## AskActionMessage

Present action choices:

### Basic Usage

```python
@cl.on_chat_start
async def start():
    response = await cl.AskActionMessage(
        content="How would you like to proceed?",
        actions=[
            cl.Action(name="continue", label="Continue", payload={"action": "continue"}),
            cl.Action(name="cancel", label="Cancel", payload={"action": "cancel"}),
        ],
        timeout=60
    ).send()

    if response:
        action = response.get("payload", {}).get("action")
        if action == "continue":
            await cl.Message(content="Continuing...").send()
        else:
            await cl.Message(content="Cancelled.").send()
```

### With Payload Data

```python
@cl.on_chat_start
async def start():
    response = await cl.AskActionMessage(
        content="Select a plan:",
        actions=[
            cl.Action(
                name="basic",
                label="Basic ($10/mo)",
                payload={"plan": "basic", "price": 10}
            ),
            cl.Action(
                name="pro",
                label="Pro ($25/mo)",
                payload={"plan": "pro", "price": 25}
            ),
            cl.Action(
                name="enterprise",
                label="Enterprise (Custom)",
                payload={"plan": "enterprise", "price": None}
            ),
        ],
        timeout=120
    ).send()

    if response:
        plan = response.get("payload", {}).get("plan")
        price = response.get("payload", {}).get("price")

        cl.user_session.set("selected_plan", plan)
        await cl.Message(content=f"You selected the {plan} plan").send()
```

## Timeout Handling

All Ask functions return `None` on timeout:

```python
@cl.on_chat_start
async def start():
    response = await cl.AskUserMessage(
        content="Quick! Answer within 30 seconds:",
        timeout=30
    ).send()

    if response is None:
        await cl.Message(content="Time's up! Starting with defaults.").send()
        cl.user_session.set("config", get_default_config())
    else:
        await cl.Message(content=f"Got it: {response.get('output')}").send()
```

## Common Patterns

### Configuration Wizard

```python
@cl.on_chat_start
async def start():
    # Step 1: Choose mode
    mode_response = await cl.AskActionMessage(
        content="Select operating mode:",
        actions=[
            cl.Action(name="simple", label="Simple Mode"),
            cl.Action(name="advanced", label="Advanced Mode"),
        ]
    ).send()

    if not mode_response:
        return

    mode = mode_response.get("payload", {}).get("name", "simple")

    # Step 2: Upload config (advanced only)
    if mode == "advanced":
        files = await cl.AskFileMessage(
            content="Upload your config file (optional)",
            accept=[".json", ".yaml"],
            max_files=1
        ).send()

        if files:
            config = parse_config(files[0].content)
            cl.user_session.set("config", config)

    # Step 3: Get API key
    api_response = await cl.AskUserMessage(
        content="Enter your API key:"
    ).send()

    if api_response:
        cl.user_session.set("api_key", api_response.get("output"))

    await cl.Message(content="Setup complete!").send()
```

### Document Q&A Setup

```python
@cl.on_chat_start
async def start():
    await cl.Message(content="Welcome to Document Q&A!").send()

    # Upload document
    files = await cl.AskFileMessage(
        content="Please upload a PDF or text document",
        accept=["application/pdf", "text/plain"],
        max_size_mb=50
    ).send()

    if not files:
        await cl.Message(content="No file uploaded. Using sample data.").send()
        return

    file = files[0]

    # Process document
    processing_msg = cl.Message(content="Processing document...")
    await processing_msg.send()

    # Extract and index content
    content = await extract_content(file)
    await index_document(content)

    await processing_msg.remove()
    await cl.Message(
        content=f"Document '{file.name}' loaded! Ask me anything about it."
    ).send()
```

### Confirmation Before Action

```python
async def delete_with_confirmation(item_id: str):
    response = await cl.AskActionMessage(
        content=f"Are you sure you want to delete item {item_id}?",
        actions=[
            cl.Action(name="yes", label="Yes, Delete"),
            cl.Action(name="no", label="No, Cancel"),
        ]
    ).send()

    if response and response.get("payload", {}).get("name") == "yes":
        await delete_item(item_id)
        return True

    return False
```
