# Actions Reference

## Table of Contents
- [Overview](#overview)
- [Creating Actions](#creating-actions)
- [Action Callbacks](#action-callbacks)
- [Action Properties](#action-properties)
- [Removing Actions](#removing-actions)
- [Common Patterns](#common-patterns)

## Overview

Actions create interactive buttons in the chat UI. When clicked, they trigger callback functions, enabling user interaction beyond text input.

## Creating Actions

### Basic Action

```python
import chainlit as cl

@cl.action_callback("greet")
async def on_greet(action: cl.Action):
    await cl.Message(content="Hello there!").send()

@cl.on_chat_start
async def start():
    actions = [
        cl.Action(name="greet", label="Say Hello")
    ]

    await cl.Message(
        content="Click the button:",
        actions=actions
    ).send()
```

### Multiple Actions

```python
@cl.action_callback("option_a")
async def on_option_a(action: cl.Action):
    await cl.Message(content="You chose Option A").send()

@cl.action_callback("option_b")
async def on_option_b(action: cl.Action):
    await cl.Message(content="You chose Option B").send()

@cl.on_chat_start
async def start():
    actions = [
        cl.Action(name="option_a", label="Option A"),
        cl.Action(name="option_b", label="Option B"),
    ]

    await cl.Message(
        content="Choose an option:",
        actions=actions
    ).send()
```

## Action Callbacks

### Access Payload

```python
@cl.action_callback("process")
async def on_process(action: cl.Action):
    # Access payload data
    data = action.payload
    item_id = data.get("id")

    await cl.Message(content=f"Processing item {item_id}").send()

@cl.on_message
async def on_message(message: cl.Message):
    actions = [
        cl.Action(
            name="process",
            label="Process",
            payload={"id": "123", "type": "document"}
        )
    ]

    await cl.Message(
        content="Ready to process?",
        actions=actions
    ).send()
```

### Remove After Click

```python
@cl.action_callback("confirm")
async def on_confirm(action: cl.Action):
    # Remove the action button after click
    await action.remove()

    await cl.Message(content="Confirmed!").send()
```

## Action Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | Identifier matching callback name |
| `label` | str | Button text (default: name) |
| `payload` | dict | Data passed to callback |
| `icon` | str | Lucide icon name |
| `tooltip` | str | Hover text |

### With Icons

```python
actions = [
    cl.Action(
        name="download",
        label="Download",
        icon="download",  # Lucide icon
        tooltip="Download the file"
    ),
    cl.Action(
        name="share",
        label="Share",
        icon="share-2",
        tooltip="Share with others"
    ),
]
```

## Removing Actions

### Remove Single Action

```python
@cl.action_callback("dismiss")
async def on_dismiss(action: cl.Action):
    await action.remove()
```

### Remove All Actions After Selection

```python
@cl.action_callback("choice")
async def on_choice(action: cl.Action):
    # Remove this action
    await action.remove()

    # Process the choice
    choice = action.payload.get("value")
    await cl.Message(content=f"You selected: {choice}").send()
```

## Common Patterns

### Feedback Buttons

```python
@cl.action_callback("feedback_positive")
async def on_positive(action: cl.Action):
    await action.remove()
    await cl.Message(content="Thanks for the positive feedback!").send()
    # Log feedback
    await log_feedback(action.payload.get("message_id"), "positive")

@cl.action_callback("feedback_negative")
async def on_negative(action: cl.Action):
    await action.remove()
    await cl.Message(content="Thanks for the feedback. We'll improve.").send()
    await log_feedback(action.payload.get("message_id"), "negative")

@cl.on_message
async def on_message(message: cl.Message):
    response = await generate_response(message.content)

    msg = cl.Message(content=response)
    await msg.send()

    # Add feedback buttons
    actions = [
        cl.Action(
            name="feedback_positive",
            label="👍",
            payload={"message_id": msg.id}
        ),
        cl.Action(
            name="feedback_negative",
            label="👎",
            payload={"message_id": msg.id}
        ),
    ]

    await cl.Message(
        content="Was this helpful?",
        actions=actions
    ).send()
```

### Confirmation Flow

```python
@cl.action_callback("confirm_delete")
async def on_confirm(action: cl.Action):
    await action.remove()
    item_id = action.payload.get("id")
    await delete_item(item_id)
    await cl.Message(content=f"Deleted item {item_id}").send()

@cl.action_callback("cancel_delete")
async def on_cancel(action: cl.Action):
    await action.remove()
    await cl.Message(content="Deletion cancelled").send()

async def ask_delete_confirmation(item_id: str):
    actions = [
        cl.Action(
            name="confirm_delete",
            label="Yes, Delete",
            payload={"id": item_id}
        ),
        cl.Action(
            name="cancel_delete",
            label="Cancel"
        ),
    ]

    await cl.Message(
        content=f"Are you sure you want to delete item {item_id}?",
        actions=actions
    ).send()
```

### Multi-Step Wizard

```python
@cl.action_callback("step1_next")
async def on_step1(action: cl.Action):
    await action.remove()
    cl.user_session.set("step", 2)

    actions = [
        cl.Action(name="step2_next", label="Continue"),
        cl.Action(name="step2_back", label="Back"),
    ]

    await cl.Message(
        content="Step 2: Configure options",
        actions=actions
    ).send()

@cl.action_callback("step2_next")
async def on_step2(action: cl.Action):
    await action.remove()
    cl.user_session.set("step", 3)

    actions = [
        cl.Action(name="finish", label="Finish"),
        cl.Action(name="step2_back", label="Back"),
    ]

    await cl.Message(
        content="Step 3: Review and finish",
        actions=actions
    ).send()

@cl.action_callback("finish")
async def on_finish(action: cl.Action):
    await action.remove()
    await cl.Message(content="Setup complete!").send()
```

### Dynamic Actions Based on State

```python
@cl.on_message
async def on_message(message: cl.Message):
    user = cl.user_session.get("user")

    actions = [
        cl.Action(name="view", label="View Details"),
    ]

    # Add admin actions
    if user and user.role == "admin":
        actions.extend([
            cl.Action(name="edit", label="Edit"),
            cl.Action(name="delete", label="Delete"),
        ])

    await cl.Message(
        content="Item found",
        actions=actions
    ).send()
```
