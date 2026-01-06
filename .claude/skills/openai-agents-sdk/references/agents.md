# Agents Reference

## Table of Contents
- [Creating Agents](#creating-agents)
- [Configuration Properties](#configuration-properties)
- [Dynamic Instructions](#dynamic-instructions)
- [Structured Outputs](#structured-outputs)
- [Context and Dependency Injection](#context-and-dependency-injection)
- [Lifecycle Hooks](#lifecycle-hooks)
- [Cloning Agents](#cloning-agents)

## Creating Agents

Basic agent creation with essential properties:

```python
from agents import Agent, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Weather Agent",
    instructions="You are a helpful weather assistant",
    model="gpt-4.1",
    tools=[get_weather],
)
```

## Configuration Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | Required identifier for the agent |
| `instructions` | str/Callable | System prompt (static or dynamic) |
| `model` | str | LLM model to use (default: gpt-4.1) |
| `tools` | list | Functions the agent can invoke |
| `handoffs` | list | Agents to delegate to |
| `output_type` | type | Pydantic model for structured output |
| `input_guardrails` | list | Input validation guardrails |
| `output_guardrails` | list | Output validation guardrails |

## Dynamic Instructions

Generate instructions based on runtime context:

```python
from agents import Agent, RunContextWrapper

def dynamic_instructions(
    ctx: RunContextWrapper[MyContext],
    agent: Agent[MyContext]
) -> str:
    user_name = ctx.context.user_name
    return f"You are helping {user_name}. Be friendly and helpful."

agent = Agent(
    name="Dynamic Agent",
    instructions=dynamic_instructions,
)
```

Async version:

```python
async def async_instructions(
    ctx: RunContextWrapper[MyContext],
    agent: Agent[MyContext]
) -> str:
    user_data = await fetch_user_data(ctx.context.user_id)
    return f"Help {user_data.name} with their {user_data.plan} plan."
```

## Structured Outputs

Force agents to return specific data structures using Pydantic:

```python
from pydantic import BaseModel
from agents import Agent

class WeatherReport(BaseModel):
    city: str
    temperature: float
    conditions: str
    humidity: int

agent = Agent(
    name="Weather Reporter",
    instructions="Extract weather information",
    output_type=WeatherReport,
)

# Result will be a WeatherReport instance
result = Runner.run_sync(agent, "What's the weather in NYC?")
report: WeatherReport = result.final_output
```

## Context and Dependency Injection

Share state across tools and handoffs using typed context:

```python
from dataclasses import dataclass
from agents import Agent, RunContextWrapper, function_tool

@dataclass
class AppContext:
    user_id: str
    db_connection: DatabaseConnection
    api_client: APIClient

@function_tool
def get_user_orders(ctx: RunContextWrapper[AppContext]) -> str:
    """Get orders for the current user."""
    orders = ctx.context.db_connection.query_orders(ctx.context.user_id)
    return str(orders)

agent = Agent[AppContext](
    name="Order Agent",
    instructions="Help users with their orders",
    tools=[get_user_orders],
)

# Pass context when running
context = AppContext(user_id="123", db_connection=db, api_client=api)
result = await Runner.run(agent, "Show my orders", context=context)
```

## Lifecycle Hooks

Observe agent execution with custom handlers:

```python
from agents import Agent, AgentHooks, RunContextWrapper

class MyHooks(AgentHooks):
    async def on_start(self, ctx: RunContextWrapper, agent: Agent):
        print(f"Agent {agent.name} starting")

    async def on_end(self, ctx: RunContextWrapper, agent: Agent, output):
        print(f"Agent {agent.name} finished with: {output}")

    async def on_tool_start(self, ctx, agent, tool):
        print(f"Calling tool: {tool.name}")

    async def on_tool_end(self, ctx, agent, tool, result):
        print(f"Tool {tool.name} returned: {result}")

agent = Agent(
    name="Observed Agent",
    instructions="Do something",
    hooks=MyHooks(),
)
```

## Cloning Agents

Create agent variants with modified properties:

```python
base_agent = Agent(
    name="Base Agent",
    instructions="You are helpful",
    model="gpt-4.1",
)

# Clone with different instructions
specialized_agent = base_agent.clone(
    name="Specialized Agent",
    instructions="You are a Python expert",
)

# Clone with additional tools
agent_with_tools = base_agent.clone(
    tools=[my_tool],
)
```
