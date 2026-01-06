# Tools Reference

## Table of Contents
- [Tool Types](#tool-types)
- [Function Tools](#function-tools)
- [Docstring Parsing](#docstring-parsing)
- [Rich Return Types](#rich-return-types)
- [Hosted Tools](#hosted-tools)
- [Agent as Tool](#agent-as-tool)
- [Tool Control](#tool-control)
- [Error Handling](#error-handling)

## Tool Types

The SDK supports three categories:

1. **Function Tools** - Python functions converted to tools
2. **Hosted Tools** - Run on LLM servers (web search, code execution)
3. **Agent Tools** - Call agents without handoffs

## Function Tools

### Basic Decorator Usage

```python
from agents import function_tool

@function_tool
def calculate_sum(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number
    """
    return a + b
```

### With Pydantic Models

```python
from pydantic import BaseModel
from agents import function_tool

class Location(BaseModel):
    city: str
    country: str

@function_tool
def get_weather(location: Location) -> str:
    """Fetch weather for a location.

    Args:
        location: The location to check weather for.
    """
    return f"Weather in {location.city}, {location.country}: Sunny"
```

### Async Tools

```python
@function_tool
async def fetch_data(url: str) -> str:
    """Fetch data from a URL.

    Args:
        url: The URL to fetch from.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

### Custom Tool Names

```python
@function_tool(name_override="search_web")
def web_search(query: str) -> str:
    """Search the web for information."""
    return search_results
```

## Docstring Parsing

The SDK extracts descriptions from docstrings. Supported formats:

**Google Style:**
```python
@function_tool
def example(param: str) -> str:
    """Short description.

    Args:
        param: Description of the parameter.

    Returns:
        Description of return value.
    """
```

**NumPy Style:**
```python
@function_tool
def example(param: str) -> str:
    """Short description.

    Parameters
    ----------
    param : str
        Description of the parameter.
    """
```

Disable docstring parsing:

```python
@function_tool(use_docstring_info=False)
def my_tool(x: int) -> int:
    """This docstring will be ignored."""
    return x * 2
```

## Rich Return Types

Return images, files, or structured content:

```python
from agents import function_tool
from agents.tool_output import ToolOutputImage, ToolOutputFileContent, ToolOutputText

@function_tool
def generate_chart(data: list) -> ToolOutputImage:
    """Generate a chart from data."""
    # Create chart...
    image_bytes = create_chart(data)
    return ToolOutputImage(data=base64.b64encode(image_bytes).decode())

@function_tool
def read_file(path: str) -> ToolOutputFileContent:
    """Read a file's contents."""
    with open(path, 'rb') as f:
        return ToolOutputFileContent(
            data=base64.b64encode(f.read()).decode(),
            mime_type="application/pdf"
        )

@function_tool
def format_response(text: str) -> ToolOutputText:
    """Format text response."""
    return ToolOutputText(text=f"Formatted: {text}")
```

## Hosted Tools

Use tools that run on the LLM server:

```python
from agents import Agent
from agents.tool import WebSearchTool, FileSearchTool, CodeInterpreterTool

agent = Agent(
    name="Research Agent",
    instructions="Research topics thoroughly",
    tools=[
        WebSearchTool(),                    # Web search
        FileSearchTool(vector_store_ids=["vs_123"]),  # File retrieval
        CodeInterpreterTool(),              # Code execution
    ],
)
```

## Agent as Tool

Call another agent as a tool (maintains conversation control):

```python
from agents import Agent, agent_tool

research_agent = Agent(
    name="Researcher",
    instructions="Research topics in depth",
)

@agent_tool(research_agent)
def research(topic: str) -> str:
    """Research a topic thoroughly."""
    pass  # Implementation handled by the agent

main_agent = Agent(
    name="Assistant",
    instructions="Help users with various tasks",
    tools=[research],
)
```

## Tool Control

### Force Tool Usage

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Tool Agent",
    instructions="Always use tools",
    tools=[my_tool],
    model_settings=ModelSettings(tool_choice="required"),
)
```

Tool choice options:
- `"auto"` - LLM decides (default)
- `"required"` - Must use a tool
- `"none"` - Cannot use tools
- `"tool_name"` - Must use specific tool

### Tool Use Behavior

```python
from agents import Agent, StopAtTools

# Stop after first tool call
agent = Agent(
    name="Single Tool Agent",
    tool_use_behavior="stop_on_first_tool",
)

# Stop at specific tools
agent = Agent(
    name="Selective Stop Agent",
    tool_use_behavior=StopAtTools(["final_answer", "submit"]),
)
```

### Conditional Tool Enabling

```python
from agents import function_tool, RunContextWrapper

@function_tool
def admin_action(ctx: RunContextWrapper[AppContext]) -> str:
    """Perform admin action (admin only)."""
    return "Admin action performed"

# Dynamic enabling based on context
admin_action.is_enabled = lambda ctx: ctx.context.user_role == "admin"
```

## Error Handling

Provide user-friendly error messages:

```python
from agents import function_tool

def handle_error(ctx, error):
    return f"Sorry, I couldn't complete that action: {str(error)}"

@function_tool(failure_error_function=handle_error)
def risky_operation(data: str) -> str:
    """Perform a risky operation."""
    # May raise exceptions
    return process(data)
```
