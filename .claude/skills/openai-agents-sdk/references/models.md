# Models Reference

## Table of Contents
- [Default Models](#default-models)
- [OpenAI Models](#openai-models)
- [LiteLLM Integration](#litellm-integration)
- [Multi-Model Workflows](#multi-model-workflows)
- [Model Settings](#model-settings)
- [Common Issues](#common-issues)

## Default Models

The SDK defaults to `gpt-4.1`. Change globally via environment:

```bash
export OPENAI_DEFAULT_MODEL=gpt-5-mini
```

Or per-agent:

```python
from agents import Agent

agent = Agent(
    name="Assistant",
    instructions="Be helpful",
    model="gpt-5-nano",  # Override default
)
```

## OpenAI Models

### Model Options

| Model | Best For |
|-------|----------|
| `gpt-4.1` | Default, balanced performance |
| `gpt-5` | Highest quality |
| `gpt-5-mini` | Good quality, faster |
| `gpt-5-nano` | Fast, cost-effective |

### GPT-5 Configuration

GPT-5 models support reasoning configuration:

```python
from agents import Agent, ModelSettings, Reasoning

agent = Agent(
    name="Reasoning Agent",
    instructions="Solve complex problems",
    model="gpt-5",
    model_settings=ModelSettings(
        reasoning=Reasoning(
            effort="high",      # low, medium, high
            verbosity="medium",  # low, medium, high
        )
    ),
)
```

### API Selection

```python
from agents import set_default_openai_api

# Use Responses API (default, recommended)
set_default_openai_api("responses")

# Use Chat Completions API (for compatibility)
set_default_openai_api("chat_completions")
```

## LiteLLM Integration

Use 100+ LLM providers via LiteLLM:

### Installation

```bash
pip install openai-agents[litellm]
```

### Usage

Prefix model names with `litellm/`:

```python
from agents import Agent

# Anthropic Claude
claude_agent = Agent(
    name="Claude Agent",
    instructions="Be helpful",
    model="litellm/anthropic/claude-sonnet-4-20250514",
)

# Google Gemini
gemini_agent = Agent(
    name="Gemini Agent",
    instructions="Be helpful",
    model="litellm/gemini/gemini-2.5-flash-preview-04-17",
)

# AWS Bedrock
bedrock_agent = Agent(
    name="Bedrock Agent",
    instructions="Be helpful",
    model="litellm/bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
)

# Azure OpenAI
azure_agent = Agent(
    name="Azure Agent",
    instructions="Be helpful",
    model="litellm/azure/gpt-4",
)
```

### Environment Variables

Set provider credentials:

```bash
# Anthropic
export ANTHROPIC_API_KEY=your-key

# Google
export GEMINI_API_KEY=your-key

# Azure
export AZURE_API_KEY=your-key
export AZURE_API_BASE=https://your-resource.openai.azure.com
export AZURE_API_VERSION=2024-02-15-preview
```

## Multi-Model Workflows

Different agents can use different models:

```python
from agents import Agent, Runner

# Fast triage with small model
triage_agent = Agent(
    name="Triage",
    instructions="Route to appropriate agent",
    model="gpt-5-nano",
    handoffs=[specialist_agent],
)

# Complex analysis with powerful model
specialist_agent = Agent(
    name="Specialist",
    instructions="Perform detailed analysis",
    model="gpt-5",
)

# Mix OpenAI and other providers
research_agent = Agent(
    name="Researcher",
    instructions="Research topics thoroughly",
    model="litellm/anthropic/claude-sonnet-4-20250514",
)

coordinator = Agent(
    name="Coordinator",
    instructions="Coordinate research tasks",
    model="gpt-4.1",
    handoffs=[research_agent],
)
```

## Model Settings

Fine-tune model behavior:

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Creative Writer",
    instructions="Write creative content",
    model_settings=ModelSettings(
        temperature=0.9,        # Higher for creativity
        max_tokens=4096,        # Longer outputs
        top_p=0.95,
        tool_choice="auto",     # auto, required, none, or tool name
    ),
)

# Structured output agent
structured_agent = Agent(
    name="Data Extractor",
    instructions="Extract structured data",
    model_settings=ModelSettings(
        temperature=0.0,        # Deterministic
        tool_choice="required", # Must use tools
    ),
)
```

## Common Issues

### Tracing Errors with Non-OpenAI Models

```python
from agents import RunConfig

# Disable tracing
config = RunConfig(tracing_disabled=True)
result = await Runner.run(agent, "Hello", run_config=config)

# Or via environment
# export OPENAI_AGENTS_DISABLE_TRACING=1
```

### Structured Output Compatibility

Many providers don't support JSON schema enforcement:

```python
# For providers without structured output support,
# use prompting instead of output_type

agent = Agent(
    name="Extractor",
    instructions="""Extract data and respond in JSON format:
    {"name": "string", "age": number}
    """,
    model="litellm/anthropic/claude-sonnet-4-20250514",
    # Don't use output_type with incompatible providers
)
```

### API Compatibility

For OpenAI-compatible endpoints:

```python
from agents import set_default_openai_client
from openai import OpenAI

# Custom endpoint
client = OpenAI(
    api_key="your-key",
    base_url="https://your-endpoint.com/v1",
)
set_default_openai_client(client)
```

## Complete Example

Multi-provider research system:

```python
from agents import Agent, Runner, function_tool

@function_tool
def search_web(query: str) -> str:
    """Search the web."""
    return f"Results for: {query}"

# Fast classifier (OpenAI)
classifier = Agent(
    name="Classifier",
    instructions="Classify query type: research, creative, or technical",
    model="gpt-5-nano",
)

# Deep research (Claude)
researcher = Agent(
    name="Researcher",
    instructions="Conduct thorough research",
    model="litellm/anthropic/claude-sonnet-4-20250514",
    tools=[search_web],
)

# Creative writing (GPT-5)
writer = Agent(
    name="Writer",
    instructions="Write creative content",
    model="gpt-5",
    model_settings=ModelSettings(temperature=0.9),
)

# Coordinator routes to specialists
coordinator = Agent(
    name="Coordinator",
    instructions="Route to the best agent for the task",
    model="gpt-4.1",
    handoffs=[classifier, researcher, writer],
)
```
