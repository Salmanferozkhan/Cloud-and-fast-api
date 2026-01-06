# Guardrails Reference

## Table of Contents
- [Overview](#overview)
- [Input Guardrails](#input-guardrails)
- [Output Guardrails](#output-guardrails)
- [Tripwires](#tripwires)
- [Execution Modes](#execution-modes)
- [Using Agents as Guardrails](#using-agents-as-guardrails)

## Overview

Guardrails validate agent inputs and outputs to prevent misuse, catch problematic requests, and ensure quality responses. They run checks before expensive model operations occur.

## Input Guardrails

Validate user input before agent execution:

```python
from agents import Agent, input_guardrail, GuardrailFunctionOutput, RunContextWrapper

@input_guardrail
async def block_profanity(
    ctx: RunContextWrapper,
    agent: Agent,
    input_text: str
) -> GuardrailFunctionOutput:
    """Block messages containing profanity."""
    has_profanity = check_profanity(input_text)
    return GuardrailFunctionOutput(
        output_info={"checked": True, "has_profanity": has_profanity},
        tripwire_triggered=has_profanity,
    )

agent = Agent(
    name="Safe Agent",
    instructions="Be helpful",
    input_guardrails=[block_profanity],
)
```

## Output Guardrails

Validate agent responses after execution:

```python
from agents import Agent, output_guardrail, GuardrailFunctionOutput

@output_guardrail
async def check_pii(
    ctx: RunContextWrapper,
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
    """Ensure no PII in responses."""
    contains_pii = detect_pii(output)
    return GuardrailFunctionOutput(
        output_info={"pii_detected": contains_pii},
        tripwire_triggered=contains_pii,
    )

agent = Agent(
    name="Privacy Agent",
    instructions="Help users",
    output_guardrails=[check_pii],
)
```

## Tripwires

When a guardrail detects an issue, it triggers a tripwire that raises an exception:

```python
from agents import Runner, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered

try:
    result = await Runner.run(agent, user_input)
except InputGuardrailTripwireTriggered as e:
    print(f"Input blocked: {e.guardrail_result.output_info}")
    # Handle blocked input
except OutputGuardrailTripwireTriggered as e:
    print(f"Output blocked: {e.guardrail_result.output_info}")
    # Handle blocked output
```

## Execution Modes

### Parallel Mode (Default)

Guardrail runs concurrently with agent for better latency:

```python
from agents import InputGuardrailExecutionMode

@input_guardrail(execution_mode=InputGuardrailExecutionMode.PARALLEL)
async def fast_check(ctx, agent, input_text):
    # Runs alongside agent execution
    return GuardrailFunctionOutput(
        output_info={},
        tripwire_triggered=False,
    )
```

**Risk:** Agent may consume tokens before guardrail completes.

### Blocking Mode

Guardrail must complete before agent starts:

```python
@input_guardrail(execution_mode=InputGuardrailExecutionMode.BLOCKING)
async def strict_check(ctx, agent, input_text):
    # Agent waits for this to complete
    return GuardrailFunctionOutput(
        output_info={},
        tripwire_triggered=False,
    )
```

**Benefit:** Prevents token consumption on blocked requests.

## Using Agents as Guardrails

Use a dedicated agent to perform validation:

```python
from agents import Agent, input_guardrail, GuardrailFunctionOutput, Runner

# Validator agent
validator = Agent(
    name="Content Validator",
    instructions="""Analyze if the input is appropriate.
    Respond with JSON: {"appropriate": true/false, "reason": "explanation"}""",
    output_type=ValidationResult,
)

@input_guardrail
async def agent_validation(ctx, agent, input_text):
    result = await Runner.run(validator, input_text)
    validation = result.final_output
    return GuardrailFunctionOutput(
        output_info={"reason": validation.reason},
        tripwire_triggered=not validation.appropriate,
    )

main_agent = Agent(
    name="Main Agent",
    instructions="Help users",
    input_guardrails=[agent_validation],
)
```

## Complete Example

Content moderation system:

```python
from pydantic import BaseModel
from agents import (
    Agent, Runner,
    input_guardrail, output_guardrail,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)

class ModerationResult(BaseModel):
    safe: bool
    category: str
    confidence: float

# Moderation agent
moderator = Agent(
    name="Moderator",
    instructions="Classify content safety. Categories: safe, hate, violence, spam",
    output_type=ModerationResult,
)

@input_guardrail
async def moderate_input(ctx, agent, input_text):
    result = await Runner.run(moderator, f"Classify: {input_text}")
    mod = result.final_output
    return GuardrailFunctionOutput(
        output_info={"category": mod.category, "confidence": mod.confidence},
        tripwire_triggered=not mod.safe,
    )

@output_guardrail
async def moderate_output(ctx, agent, output):
    result = await Runner.run(moderator, f"Classify: {output}")
    mod = result.final_output
    return GuardrailFunctionOutput(
        output_info={"category": mod.category},
        tripwire_triggered=not mod.safe,
    )

# Main agent with guardrails
assistant = Agent(
    name="Safe Assistant",
    instructions="Be helpful and appropriate",
    input_guardrails=[moderate_input],
    output_guardrails=[moderate_output],
)

# Usage
async def chat(user_message: str) -> str:
    try:
        result = await Runner.run(assistant, user_message)
        return result.final_output
    except InputGuardrailTripwireTriggered as e:
        return f"I can't respond to that type of message."
    except OutputGuardrailTripwireTriggered:
        return "I generated an inappropriate response. Please try again."
```
