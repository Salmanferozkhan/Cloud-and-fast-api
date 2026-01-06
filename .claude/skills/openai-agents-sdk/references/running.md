# Running Agents Reference

## Table of Contents
- [Runner Class](#runner-class)
- [Run Methods](#run-methods)
- [The Agent Loop](#the-agent-loop)
- [Streaming](#streaming)
- [Run Configuration](#run-configuration)
- [Result Handling](#result-handling)
- [Exception Handling](#exception-handling)

## Runner Class

The `Runner` class executes agents and manages the conversation loop:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Be helpful")

# Async execution
result = await Runner.run(agent, "Hello!")

# Sync execution
result = Runner.run_sync(agent, "Hello!")

# Streaming execution
result = await Runner.run_streamed(agent, "Hello!")
```

## Run Methods

### `Runner.run()` - Async

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Be helpful")

async def main():
    result = await Runner.run(agent, "What is 2+2?")
    print(result.final_output)
```

### `Runner.run_sync()` - Synchronous

```python
# Blocking call, runs async internally
result = Runner.run_sync(agent, "What is 2+2?")
print(result.final_output)
```

### `Runner.run_streamed()` - Streaming

```python
async def stream_response():
    result = await Runner.run_streamed(agent, "Write a story")

    async for event in result.stream_events():
        if event.type == "text_delta":
            print(event.delta, end="", flush=True)

    print(f"\nFinal: {result.final_output}")
```

## The Agent Loop

Runner processes steps sequentially:

1. **Invoke LLM** with current agent and input
2. **Process output:**
   - If `final_output` -> terminate and return
   - If handoff -> switch to new agent, continue loop
   - If tool calls -> execute tools, continue loop
3. **Check limits** -> raise `MaxTurnsExceeded` if exceeded

```python
# Control max iterations
result = await Runner.run(
    agent,
    "Complex task",
    max_turns=10,  # Default is reasonable
)
```

## Streaming

Real-time event streaming:

```python
from agents import Agent, Runner

agent = Agent(name="Writer", instructions="Write detailed content")

async def stream_with_events():
    result = await Runner.run_streamed(agent, "Write about AI")

    async for event in result.stream_events():
        match event.type:
            case "text_delta":
                # Partial text output
                print(event.delta, end="")
            case "tool_call_start":
                # Tool invocation beginning
                print(f"\nCalling tool: {event.tool_name}")
            case "tool_call_end":
                # Tool completed
                print(f"Tool result: {event.result}")
            case "handoff":
                # Agent handoff occurred
                print(f"Handed off to: {event.target_agent}")

    # Access complete result after streaming
    print(f"\n\nComplete output: {result.final_output}")
```

## Run Configuration

Customize execution with `RunConfig`:

```python
from agents import Agent, Runner, RunConfig

config = RunConfig(
    # Model settings
    model="gpt-4.1",

    # Guardrails
    input_guardrails=[my_input_guard],
    output_guardrails=[my_output_guard],

    # Tracing
    workflow_name="customer_support",
    trace_id="unique-trace-id",
    trace_metadata={"user_id": "123"},
    tracing_disabled=False,

    # Limits
    max_turns=20,
)

result = await Runner.run(agent, "Hello", run_config=config)
```

## Result Handling

### RunResult Properties

```python
result = await Runner.run(agent, "Hello")

# Final output (string or structured type)
output = result.final_output

# All items from the run
for item in result.new_items:
    match item:
        case MessageOutputItem():
            print(f"Message: {item.content}")
        case ToolCallItem():
            print(f"Tool call: {item.tool_name}")
        case ToolCallOutputItem():
            print(f"Tool result: {item.output}")
        case HandoffCallItem():
            print(f"Handoff to: {item.target_agent}")

# Last agent that ran
final_agent = result.last_agent

# Guardrail results
input_results = result.input_guardrail_results
output_results = result.output_guardrail_results

# Convert to input for next turn
next_input = result.to_input_list()
```

### Continuing Conversations

```python
# Manual conversation management
result1 = await Runner.run(agent, "My name is Bob")
result2 = await Runner.run(agent, result1.to_input_list() + ["What's my name?"])

# Or use sessions (recommended)
from agents.extensions.session import SQLiteSession
session = SQLiteSession("user_123")
result = await Runner.run(agent, "Hello", session=session)
```

## Exception Handling

```python
from agents import (
    Runner,
    MaxTurnsExceeded,
    ModelBehaviorError,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)

async def safe_run(agent, input_text):
    try:
        result = await Runner.run(agent, input_text)
        return result.final_output

    except MaxTurnsExceeded:
        return "The conversation got too long. Please try a simpler request."

    except ModelBehaviorError as e:
        return f"The model behaved unexpectedly: {e}"

    except InputGuardrailTripwireTriggered as e:
        return f"Input blocked: {e.guardrail_result.output_info}"

    except OutputGuardrailTripwireTriggered as e:
        return f"Output blocked: {e.guardrail_result.output_info}"
```

## Complete Example

Full-featured agent execution:

```python
from agents import Agent, Runner, RunConfig, function_tool
from agents.extensions.session import SQLiteSession

@function_tool
def get_time() -> str:
    """Get current time."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

agent = Agent(
    name="Time Assistant",
    instructions="Help users with time-related questions",
    tools=[get_time],
)

async def chat(user_id: str, message: str) -> str:
    session = SQLiteSession(user_id, "chats.db")

    config = RunConfig(
        workflow_name="time_assistant",
        trace_metadata={"user_id": user_id},
        max_turns=10,
    )

    try:
        result = await Runner.run(
            agent,
            message,
            session=session,
            run_config=config,
        )
        return result.final_output
    except Exception as e:
        return f"Error: {str(e)}"

# Usage
response = await chat("user_123", "What time is it?")
```
