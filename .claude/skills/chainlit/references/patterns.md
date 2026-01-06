# Common Patterns Reference

## Table of Contents
- [Simple Chatbot](#simple-chatbot)
- [RAG Application](#rag-application)
- [Document Q&A](#document-qa)
- [Multi-Agent System](#multi-agent-system)
- [Chat with Settings](#chat-with-settings)
- [Chat Profiles](#chat-profiles)
- [Feedback Collection](#feedback-collection)

## Simple Chatbot

Basic conversational AI with memory:

```python
from openai import AsyncOpenAI
import chainlit as cl

client = AsyncOpenAI()

@cl.on_chat_start
async def start():
    cl.user_session.set("history", [
        {"role": "system", "content": "You are a helpful assistant."}
    ])
    await cl.Message(content="Hello! How can I help you today?").send()

@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history")
    history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    stream = await client.chat.completions.create(
        model="gpt-4",
        messages=history,
        stream=True
    )

    response = ""
    async for chunk in stream:
        if token := chunk.choices[0].delta.content:
            response += token
            await msg.stream_token(token)

    await msg.update()

    history.append({"role": "assistant", "content": response})
    cl.user_session.set("history", history)
```

## RAG Application

Retrieval-Augmented Generation:

```python
from openai import AsyncOpenAI
import chainlit as cl

client = AsyncOpenAI()

# Simulated vector store
async def search_documents(query: str, k: int = 3) -> list:
    # Replace with actual vector search
    return [
        {"content": "Document 1 content...", "source": "doc1.pdf"},
        {"content": "Document 2 content...", "source": "doc2.pdf"},
    ]

@cl.step(name="Search Documents", type="retrieval")
async def retrieve(query: str):
    docs = await search_documents(query)
    return "\n\n".join([d["content"] for d in docs])

@cl.step(name="Generate Answer", type="llm")
async def generate(query: str, context: str):
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"Answer based on this context:\n{context}"},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content

@cl.on_chat_start
async def start():
    await cl.Message(content="Ask me anything about the documents!").send()

@cl.on_message
async def on_message(message: cl.Message):
    context = await retrieve(message.content)
    answer = await generate(message.content, context)
    await cl.Message(content=answer).send()
```

## Document Q&A

Upload and query documents:

```python
from openai import AsyncOpenAI
import chainlit as cl

client = AsyncOpenAI()

@cl.on_chat_start
async def start():
    files = await cl.AskFileMessage(
        content="Upload a document to analyze",
        accept=["text/plain", "application/pdf"],
        max_size_mb=10
    ).send()

    if not files:
        await cl.Message(content="No file uploaded.").send()
        return

    file = files[0]

    # Process file
    processing = cl.Message(content="Processing document...")
    await processing.send()

    # Extract text (simplified)
    if file.type == "text/plain":
        content = file.content.decode("utf-8")
    else:
        content = await extract_pdf_text(file.path)

    cl.user_session.set("document", content)

    await processing.remove()
    await cl.Message(
        content=f"Document '{file.name}' loaded! Ask questions about it."
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    document = cl.user_session.get("document")

    if not document:
        await cl.Message(content="Please upload a document first.").send()
        return

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"Document:\n{document[:4000]}"},
            {"role": "user", "content": message.content}
        ]
    )

    await cl.Message(content=response.choices[0].message.content).send()
```

## Multi-Agent System

Coordinator with specialized agents:

```python
from openai import AsyncOpenAI
import chainlit as cl

client = AsyncOpenAI()

AGENTS = {
    "researcher": "You are a research assistant. Find and summarize information.",
    "coder": "You are a coding assistant. Write and explain code.",
    "writer": "You are a writing assistant. Help with content creation.",
}

@cl.step(type="tool")
async def route_to_agent(query: str) -> str:
    """Determine which agent should handle the query."""
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Classify the query. Respond with only: researcher, coder, or writer"},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content.strip().lower()

@cl.step(type="llm")
async def agent_response(agent: str, query: str) -> str:
    """Get response from specialized agent."""
    system_prompt = AGENTS.get(agent, AGENTS["researcher"])

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content

@cl.on_message
async def on_message(message: cl.Message):
    # Route to appropriate agent
    agent = await route_to_agent(message.content)

    # Get agent response
    response = await agent_response(agent, message.content)

    await cl.Message(
        content=response,
        author=agent.title()
    ).send()
```

## Chat with Settings

User-configurable chat:

```python
from openai import AsyncOpenAI
import chainlit as cl

client = AsyncOpenAI()

@cl.on_chat_start
async def start():
    settings = await cl.ChatSettings([
        cl.input_widget.Select(
            id="model",
            label="Model",
            values=["gpt-4", "gpt-3.5-turbo"],
            initial_value="gpt-4"
        ),
        cl.input_widget.Slider(
            id="temperature",
            label="Temperature",
            initial=0.7,
            min=0,
            max=1,
            step=0.1
        ),
        cl.input_widget.TextInput(
            id="system_prompt",
            label="System Prompt",
            initial="You are a helpful assistant."
        ),
    ]).send()

    cl.user_session.set("settings", settings)

@cl.on_settings_update
async def settings_update(settings):
    cl.user_session.set("settings", settings)
    await cl.Message(content="Settings updated!").send()

@cl.on_message
async def on_message(message: cl.Message):
    settings = cl.user_session.get("settings")

    response = await client.chat.completions.create(
        model=settings["model"],
        temperature=settings["temperature"],
        messages=[
            {"role": "system", "content": settings["system_prompt"]},
            {"role": "user", "content": message.content}
        ]
    )

    await cl.Message(content=response.choices[0].message.content).send()
```

## Chat Profiles

Multiple assistant configurations:

```python
from openai import AsyncOpenAI
import chainlit as cl

client = AsyncOpenAI()

PROFILES = {
    "General Assistant": {
        "model": "gpt-4",
        "system": "You are a helpful general assistant."
    },
    "Code Expert": {
        "model": "gpt-4",
        "system": "You are an expert programmer. Provide code examples."
    },
    "Creative Writer": {
        "model": "gpt-4",
        "system": "You are a creative writer. Be imaginative and expressive."
    },
}

@cl.set_chat_profiles
async def chat_profiles():
    return [
        cl.ChatProfile(
            name="General Assistant",
            markdown_description="General-purpose helpful assistant"
        ),
        cl.ChatProfile(
            name="Code Expert",
            markdown_description="Programming and code assistance"
        ),
        cl.ChatProfile(
            name="Creative Writer",
            markdown_description="Creative writing and storytelling"
        ),
    ]

@cl.on_chat_start
async def start():
    profile = cl.user_session.get("chat_profile")
    config = PROFILES.get(profile, PROFILES["General Assistant"])

    cl.user_session.set("config", config)

    await cl.Message(content=f"Hello! I'm your {profile}.").send()

@cl.on_message
async def on_message(message: cl.Message):
    config = cl.user_session.get("config")

    response = await client.chat.completions.create(
        model=config["model"],
        messages=[
            {"role": "system", "content": config["system"]},
            {"role": "user", "content": message.content}
        ]
    )

    await cl.Message(content=response.choices[0].message.content).send()
```

## Feedback Collection

Collect user feedback on responses:

```python
from openai import AsyncOpenAI
import chainlit as cl

client = AsyncOpenAI()

async def log_feedback(message_id: str, score: int, comment: str = None):
    # Save to database
    print(f"Feedback: {message_id} - Score: {score} - Comment: {comment}")

@cl.action_callback("feedback_good")
async def on_good(action: cl.Action):
    await log_feedback(action.payload["message_id"], 1)
    await action.remove()
    await cl.Message(content="Thanks for the positive feedback!").send()

@cl.action_callback("feedback_bad")
async def on_bad(action: cl.Action):
    # Ask for more details
    response = await cl.AskUserMessage(
        content="What could be improved?",
        timeout=60
    ).send()

    comment = response.get("output") if response else None
    await log_feedback(action.payload["message_id"], -1, comment)
    await action.remove()
    await cl.Message(content="Thanks for the feedback!").send()

@cl.on_message
async def on_message(message: cl.Message):
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": message.content}]
    )

    msg = cl.Message(content=response.choices[0].message.content)
    await msg.send()

    # Add feedback buttons
    actions = [
        cl.Action(
            name="feedback_good",
            label="👍 Helpful",
            payload={"message_id": msg.id}
        ),
        cl.Action(
            name="feedback_bad",
            label="👎 Not helpful",
            payload={"message_id": msg.id}
        ),
    ]

    await cl.Message(
        content="Was this response helpful?",
        actions=actions
    ).send()
```
