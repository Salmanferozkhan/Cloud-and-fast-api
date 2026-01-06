# Authentication Reference

## Table of Contents
- [Overview](#overview)
- [Setup](#setup)
- [Password Authentication](#password-authentication)
- [OAuth Authentication](#oauth-authentication)
- [Header Authentication](#header-authentication)
- [Accessing User Info](#accessing-user-info)
- [Protected Routes](#protected-routes)

## Overview

Chainlit supports three authentication methods:
- Password authentication (username/password)
- OAuth (Google, GitHub, etc.)
- Header-based (custom headers)

By default, apps are public. Adding auth makes them private.

## Setup

### Generate Auth Secret

```bash
chainlit create-secret
```

### Set Environment Variable

```bash
# .env file
CHAINLIT_AUTH_SECRET=your-generated-secret-key
```

**Important**: Each user must have a unique identifier to prevent data sharing.

## Password Authentication

### Basic Implementation

```python
import chainlit as cl

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Validate credentials
    if username == "admin" and password == "admin123":
        return cl.User(
            identifier="admin",
            metadata={"role": "admin", "provider": "credentials"}
        )

    if username == "user" and password == "user123":
        return cl.User(
            identifier="user",
            metadata={"role": "user", "provider": "credentials"}
        )

    # Return None for failed auth
    return None
```

### Database Integration

```python
import chainlit as cl
import bcrypt

@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    # Fetch user from database
    user = await db.get_user(username)

    if not user:
        return None

    # Verify password
    if bcrypt.checkpw(password.encode(), user.password_hash):
        return cl.User(
            identifier=user.id,
            metadata={
                "role": user.role,
                "email": user.email,
                "provider": "credentials"
            }
        )

    return None
```

## OAuth Authentication

### Google OAuth

```python
import chainlit as cl

@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict,
    default_user: cl.User
) -> cl.User:
    if provider_id == "google":
        return cl.User(
            identifier=raw_user_data["email"],
            metadata={
                "name": raw_user_data.get("name"),
                "picture": raw_user_data.get("picture"),
                "provider": "google"
            }
        )

    return default_user
```

### Configuration

```toml
# .chainlit/config.toml

[project]
enable_telemetry = false

[features.oauth]
# Google
google_client_id = "your-client-id"
google_client_secret = "your-client-secret"

# GitHub
github_client_id = "your-client-id"
github_client_secret = "your-client-secret"
```

### Environment Variables Alternative

```bash
# .env
OAUTH_GOOGLE_CLIENT_ID=your-client-id
OAUTH_GOOGLE_CLIENT_SECRET=your-client-secret
```

### Multiple Providers

```python
@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict,
    default_user: cl.User
) -> cl.User:
    if provider_id == "google":
        return cl.User(
            identifier=raw_user_data["email"],
            metadata={"provider": "google", "name": raw_user_data.get("name")}
        )

    if provider_id == "github":
        return cl.User(
            identifier=str(raw_user_data["id"]),
            metadata={"provider": "github", "username": raw_user_data.get("login")}
        )

    return default_user
```

## Header Authentication

For custom authentication systems (API gateways, proxies):

```python
import chainlit as cl

@cl.header_auth_callback
def header_auth_callback(headers: dict) -> cl.User:
    # Check for auth header
    auth_token = headers.get("X-Auth-Token")

    if not auth_token:
        return None

    # Validate token
    user_data = validate_token(auth_token)

    if user_data:
        return cl.User(
            identifier=user_data["user_id"],
            metadata={
                "role": user_data["role"],
                "provider": "header"
            }
        )

    return None
```

### JWT Validation

```python
import jwt
import chainlit as cl

SECRET_KEY = "your-secret-key"

@cl.header_auth_callback
def header_auth_callback(headers: dict) -> cl.User:
    auth_header = headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]  # Remove "Bearer " prefix

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return cl.User(
            identifier=payload["sub"],
            metadata={
                "role": payload.get("role"),
                "provider": "jwt"
            }
        )
    except jwt.InvalidTokenError:
        return None
```

## Accessing User Info

### In Chat Handlers

```python
@cl.on_chat_start
async def start():
    user = cl.user_session.get("user")

    if user:
        name = user.metadata.get("name", user.identifier)
        role = user.metadata.get("role", "user")

        await cl.Message(
            content=f"Welcome, {name}! You have {role} access."
        ).send()
```

### Role-Based Access

```python
@cl.on_message
async def on_message(message: cl.Message):
    user = cl.user_session.get("user")

    if message.content.startswith("/admin"):
        if user.metadata.get("role") != "admin":
            await cl.Message(content="Access denied. Admin only.").send()
            return

        # Handle admin command
        await handle_admin_command(message.content)
    else:
        # Regular message handling
        await handle_message(message.content)
```

### Store User-Specific Data

```python
@cl.on_chat_start
async def start():
    user = cl.user_session.get("user")

    # Load user preferences from database
    prefs = await load_user_preferences(user.identifier)
    cl.user_session.set("preferences", prefs)

@cl.on_chat_end
async def end():
    user = cl.user_session.get("user")
    prefs = cl.user_session.get("preferences")

    # Save preferences
    await save_user_preferences(user.identifier, prefs)
```

## Protected Routes

### Conditional Features

```python
@cl.on_chat_start
async def start():
    user = cl.user_session.get("user")
    role = user.metadata.get("role", "user")

    # Set available features based on role
    if role == "admin":
        cl.user_session.set("features", ["basic", "advanced", "admin"])
    elif role == "premium":
        cl.user_session.set("features", ["basic", "advanced"])
    else:
        cl.user_session.set("features", ["basic"])

@cl.on_message
async def on_message(message: cl.Message):
    features = cl.user_session.get("features", ["basic"])

    if "/advanced" in message.content and "advanced" not in features:
        await cl.Message(content="Upgrade to premium for this feature.").send()
        return

    # Process message
```

## Complete Example

```python
import chainlit as cl
from openai import AsyncOpenAI

client = AsyncOpenAI()

@cl.password_auth_callback
def auth(username: str, password: str):
    users = {
        "admin": {"password": "admin123", "role": "admin"},
        "user": {"password": "user123", "role": "user"},
    }

    user = users.get(username)
    if user and user["password"] == password:
        return cl.User(
            identifier=username,
            metadata={"role": user["role"]}
        )
    return None

@cl.on_chat_start
async def start():
    user = cl.user_session.get("user")
    role = user.metadata.get("role")

    # Set model based on role
    model = "gpt-4" if role == "admin" else "gpt-3.5-turbo"
    cl.user_session.set("model", model)

    await cl.Message(
        content=f"Welcome {user.identifier}! Using {model}."
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    model = cl.user_session.get("model")

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message.content}]
    )

    await cl.Message(content=response.choices[0].message.content).send()
```
