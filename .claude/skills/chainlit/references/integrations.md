# Integrations Reference

## Table of Contents
- [OpenAI Agents SDK](#openai-agents-sdk)
- [OpenAI](#openai)
- [LangChain](#langchain)
- [LlamaIndex](#llamaindex)
- [Mistral AI](#mistral-ai)
- [LiteLLM](#litellm)

## OpenAI Agents SDK

Integration with the OpenAI Agents SDK for multi-agent workflows with streaming.

### Setup

```bash
pip install openai-agents chainlit python-dotenv
```

### Basic Streaming Integration

```python
"""OpenAI Agents SDK with Chainlit streaming.

Run with: chainlit run app.py -w
"""
import json
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())  # Load API keys BEFORE importing agent

import chainlit as cl
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny, 72°F"

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    tools=[get_weather],
)


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(content="Hello! How can I help?").send()


@cl.on_message
async def on_message(message: cl.Message):
    # Build conversation context
    history = cl.user_session.get("history", [])
    input_messages = []
    for h in history:
        input_messages.append({"role": "user", "content": h["user"]})
        input_messages.append({"role": "assistant", "content": h["assistant"]})
    input_messages.append({"role": "user", "content": message.content})

    # Create streaming message
    msg = cl.Message(content="")
    await msg.send()

    # Run with streaming (not awaited!)
    result = Runner.run_streamed(agent, input_messages)

    full_response = ""
    tool_calls = {}

    async for event in result.stream_events():
        # Stream text tokens
        if event.type == "raw_response_event":
            if hasattr(event.data, "delta") and event.data.delta:
                full_response += event.data.delta
                await msg.stream_token(event.data.delta)

        # Show tool calls as steps
        elif event.type == "run_item_stream_event":
            item = event.item
            item_type = getattr(item, "type", None)

            if item_type == "tool_call_item":
                tool_name = getattr(item, "name", "tool")
                tool_call_id = getattr(item, "call_id", id(item))
                raw_args = getattr(item, "arguments", "{}")

                try:
                    args = json.loads(raw_args) if raw_args else {}
                    args_display = json.dumps(args, indent=2)
                except (json.JSONDecodeError, TypeError):
                    args_display = str(raw_args)

                step = cl.Step(name=tool_name, type="tool")
                step.input = args_display
                await step.send()
                tool_calls[tool_call_id] = step

            elif item_type == "tool_call_output_item":
                tool_call_id = getattr(item, "call_id", None)
                output = getattr(item, "output", "")

                if tool_call_id and tool_call_id in tool_calls:
                    step = tool_calls[tool_call_id]
                    step.output = output
                    await step.update()

    await msg.update()

    # Update history
    history.append({"user": message.content, "assistant": full_response})
    if len(history) > 10:
        history = history[-10:]
    cl.user_session.set("history", history)
```

### Key Event Types

| Event Type | Description |
|------------|-------------|
| `raw_response_event` | Text streaming, check `event.data.delta` |
| `run_item_stream_event` | Tool calls and results |

### Item Types in `run_item_stream_event`

| Item Type | Description |
|-----------|-------------|
| `tool_call_item` | Tool being invoked (has `name`, `call_id`, `arguments`) |
| `tool_call_output_item` | Tool result (has `call_id`, `output`) |

## OpenAI

### Setup

```bash
pip install openai chainlit
```

```bash
# .env
OPENAI_API_KEY=your-api-key
```

### Basic Integration

```python
from openai import AsyncOpenAI
import chainlit as cl

client = AsyncOpenAI()

# Instrument OpenAI for step visibility
cl.instrument_openai()

@cl.on_message
async def on_message(message: cl.Message):
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message.content}
        ]
    )

    await cl.Message(content=response.choices[0].message.content).send()
```

### Streaming

```python
from openai import AsyncOpenAI
import chainlit as cl

client = AsyncOpenAI()
cl.instrument_openai()

settings = {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 500,
}

@cl.on_chat_start
async def start():
    cl.user_session.set("messages", [
        {"role": "system", "content": "You are a helpful assistant."}
    ])

@cl.on_message
async def on_message(message: cl.Message):
    messages = cl.user_session.get("messages")
    messages.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    stream = await client.chat.completions.create(
        messages=messages,
        stream=True,
        **settings
    )

    full_response = ""
    async for chunk in stream:
        if token := chunk.choices[0].delta.content:
            full_response += token
            await msg.stream_token(token)

    await msg.update()

    messages.append({"role": "assistant", "content": full_response})
    cl.user_session.set("messages", messages)
```

### With Tools/Functions

```python
from openai import AsyncOpenAI
import chainlit as cl
import json

client = AsyncOpenAI()
cl.instrument_openai()

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"]
            }
        }
    }
]

def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny, 72°F"

@cl.on_message
async def on_message(message: cl.Message):
    messages = [{"role": "user", "content": message.content}]

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        for tool_call in msg.tool_calls:
            if tool_call.function.name == "get_weather":
                args = json.loads(tool_call.function.arguments)
                result = get_weather(args["city"])

                messages.append(msg)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

        # Get final response
        final = await client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )

        await cl.Message(content=final.choices[0].message.content).send()
    else:
        await cl.Message(content=msg.content).send()
```

## LangChain

### Setup

```bash
pip install langchain langchain-openai chainlit
```

### Basic Integration

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable.config import RunnableConfig
import chainlit as cl

@cl.on_chat_start
async def start():
    model = ChatOpenAI(streaming=True)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("human", "{question}")
    ])

    runnable = prompt | model | StrOutputParser()
    cl.user_session.set("runnable", runnable)

@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")

    msg = cl.Message(content="")
    await msg.send()

    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()])
    ):
        await msg.stream_token(chunk)

    await msg.update()
```

### LangGraph Agent

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain.schema.runnable.config import RunnableConfig
import chainlit as cl

@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Search results for: {query}"

@cl.on_chat_start
async def start():
    model = ChatOpenAI(model="gpt-4", streaming=True)
    agent = create_react_agent(model, tools=[search])
    cl.user_session.set("agent", agent)

@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent")

    msg = cl.Message(content="")
    await msg.send()

    async for event in agent.astream_events(
        {"messages": [("human", message.content)]},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
        version="v2"
    ):
        if event["event"] == "on_chat_model_stream":
            if "chunk" in event["data"]:
                token = event["data"]["chunk"].content
                if token:
                    await msg.stream_token(token)

    await msg.update()
```

## LlamaIndex

### Setup

```bash
pip install llama-index chainlit
```

### Basic RAG

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.callbacks import CallbackManager
import chainlit as cl

@cl.on_chat_start
async def start():
    # Load documents
    documents = SimpleDirectoryReader("./data").load_data()

    # Create index
    index = VectorStoreIndex.from_documents(documents)

    # Create query engine with Chainlit callbacks
    query_engine = index.as_query_engine(
        streaming=True,
        callback_manager=CallbackManager([cl.LlamaIndexCallbackHandler()])
    )

    cl.user_session.set("query_engine", query_engine)

    await cl.Message(content="Documents loaded! Ask me anything.").send()

@cl.on_message
async def on_message(message: cl.Message):
    query_engine = cl.user_session.get("query_engine")

    msg = cl.Message(content="")
    await msg.send()

    response = await cl.make_async(query_engine.query)(message.content)

    for token in response.response_gen:
        await msg.stream_token(token)

    await msg.update()
```

## Mistral AI

### Setup

```bash
pip install mistralai chainlit
```

### Basic Integration

```python
from mistralai import Mistral
import chainlit as cl

client = Mistral(api_key="your-api-key")

@cl.on_message
async def on_message(message: cl.Message):
    msg = cl.Message(content="")
    await msg.send()

    stream = await client.chat.stream_async(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": message.content}]
    )

    async for chunk in stream:
        if chunk.data.choices[0].delta.content:
            await msg.stream_token(chunk.data.choices[0].delta.content)

    await msg.update()
```

## LiteLLM

### Setup

```bash
pip install litellm chainlit
```

### Multi-Provider Support

```python
import litellm
import chainlit as cl

@cl.on_chat_start
async def start():
    # Set default model
    cl.user_session.set("model", "gpt-4")

@cl.on_message
async def on_message(message: cl.Message):
    model = cl.user_session.get("model")

    msg = cl.Message(content="")
    await msg.send()

    response = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": message.content}],
        stream=True
    )

    async for chunk in response:
        if chunk.choices[0].delta.content:
            await msg.stream_token(chunk.choices[0].delta.content)

    await msg.update()
```

### Switch Models Dynamically

```python
import litellm
import chainlit as cl

MODELS = {
    "gpt4": "gpt-4",
    "claude": "claude-3-opus-20240229",
    "gemini": "gemini-pro",
}

@cl.on_chat_start
async def start():
    settings = await cl.ChatSettings([
        cl.input_widget.Select(
            id="model",
            label="Model",
            values=list(MODELS.keys()),
            initial_value="gpt4"
        )
    ]).send()

    cl.user_session.set("model", MODELS[settings["model"]])

@cl.on_settings_update
async def settings_update(settings):
    cl.user_session.set("model", MODELS[settings["model"]])
    await cl.Message(content=f"Switched to {settings['model']}").send()

@cl.on_message
async def on_message(message: cl.Message):
    model = cl.user_session.get("model")

    response = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": message.content}]
    )

    await cl.Message(content=response.choices[0].message.content).send()
```

## Important Notes

- **Don't mix integrations**: If using LangChain or LlamaIndex, don't call `cl.instrument_openai()` to avoid duplicate steps
- **Callbacks**: Each framework has its own callback handler for step visibility
- **Streaming**: Most integrations support streaming with `stream=True` or `streaming=True`
