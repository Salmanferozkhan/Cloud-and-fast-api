# Steps Reference

## Table of Contents
- [Overview](#overview)
- [Step Types](#step-types)
- [Decorator Approach](#decorator-approach)
- [Context Manager Approach](#context-manager-approach)
- [Nested Steps](#nested-steps)
- [Step with Streaming](#step-with-streaming)
- [Configuration](#configuration)

## Overview

A Step represents a discrete processing stage in an LLM workflow. Unlike Messages, Steps have type, input/output, and start/end properties, enabling detailed tracking of the chain of thought.

## Step Types

| Type | Description |
|------|-------------|
| `llm` | Language model inference |
| `tool` | Tool/function execution |
| `retrieval` | Data retrieval operations |
| `embedding` | Embedding generation |
| `run` | Generic processing step |
| `undefined` | Default type |

## Decorator Approach

Clean syntax for step functions:

### Basic Tool Step

```python
import chainlit as cl

@cl.step(type="tool")
async def search_database(query: str):
    """Search the database for relevant information."""
    results = await db.search(query)
    return f"Found {len(results)} results"

@cl.on_message
async def on_message(message: cl.Message):
    # Step is automatically displayed in UI
    result = await search_database(message.content)
    await cl.Message(content=result).send()
```

### LLM Step

```python
@cl.step(type="llm")
async def generate_response(prompt: str):
    """Generate a response using the LLM."""
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

@cl.on_message
async def on_message(message: cl.Message):
    response = await generate_response(message.content)
    await cl.Message(content=response).send()
```

### Named Steps

```python
@cl.step(name="Web Search", type="tool")
async def search_web(query: str):
    """Search the web for information."""
    return await web_search(query)

@cl.step(name="Analyze Results", type="llm")
async def analyze(data: str):
    """Analyze the search results."""
    return await llm_analyze(data)
```

## Context Manager Approach

Flexible inline usage:

### Basic Context Manager

```python
@cl.on_message
async def on_message(message: cl.Message):
    async with cl.Step(name="Processing", type="tool") as step:
        step.input = message.content

        # Do processing
        result = await process(message.content)

        step.output = result

    await cl.Message(content=result).send()
```

### With Error Handling

```python
@cl.on_message
async def on_message(message: cl.Message):
    async with cl.Step(name="API Call", type="tool") as step:
        step.input = {"query": message.content}

        try:
            result = await external_api(message.content)
            step.output = result
        except Exception as e:
            step.output = f"Error: {str(e)}"
            step.is_error = True
            raise

    await cl.Message(content=result).send()
```

## Nested Steps

Show hierarchical processing:

```python
@cl.step(type="tool")
async def sub_task_1():
    await cl.sleep(1)
    return "Sub-task 1 complete"

@cl.step(type="tool")
async def sub_task_2():
    await cl.sleep(1)
    return "Sub-task 2 complete"

@cl.step(name="Main Task", type="run")
async def main_task():
    # These steps appear nested under main task
    result1 = await sub_task_1()
    result2 = await sub_task_2()
    return f"{result1}, {result2}"

@cl.on_message
async def on_message(message: cl.Message):
    result = await main_task()
    await cl.Message(content=result).send()
```

### Deep Nesting

```python
@cl.step(type="tool")
async def level_3():
    return "Level 3"

@cl.step(type="tool")
async def level_2():
    result = await level_3()
    return f"Level 2 -> {result}"

@cl.step(type="run")
async def level_1():
    result = await level_2()
    return f"Level 1 -> {result}"
```

## Step with Streaming

Stream content within steps:

```python
@cl.on_message
async def on_message(message: cl.Message):
    async with cl.Step(name="Generating", type="llm") as step:
        step.input = message.content

        stream = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": message.content}],
            stream=True
        )

        response = ""
        async for chunk in stream:
            if token := chunk.choices[0].delta.content:
                response += token
                await step.stream_token(token)

        step.output = response

    await cl.Message(content=response).send()
```

## Configuration

Control step visibility with config:

### Hide All Steps

In `.chainlit/config.toml`:
```toml
[UI]
cot = "hidden"  # Hide chain of thought
```

### Show Only Tool Calls

```toml
[UI]
cot = "tool_call"  # Show only tool steps
```

### Show All Steps

```toml
[UI]
cot = "full"  # Show all steps (default)
```

## Complete Example

RAG pipeline with steps:

```python
import chainlit as cl
from openai import AsyncOpenAI

client = AsyncOpenAI()

@cl.step(name="Search Documents", type="retrieval")
async def search_docs(query: str):
    """Search the document store."""
    # Simulate retrieval
    docs = await vector_store.search(query, k=3)
    return "\n".join([doc.content for doc in docs])

@cl.step(name="Generate Answer", type="llm")
async def generate_answer(query: str, context: str):
    """Generate answer from context."""
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"Context:\n{context}"},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content

@cl.on_message
async def on_message(message: cl.Message):
    # Steps are displayed in UI
    context = await search_docs(message.content)
    answer = await generate_answer(message.content, context)

    await cl.Message(content=answer).send()
```
