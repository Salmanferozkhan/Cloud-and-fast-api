# Handoffs Reference

## Table of Contents
- [Overview](#overview)
- [Basic Handoffs](#basic-handoffs)
- [Customized Handoffs](#customized-handoffs)
- [Handoff Inputs](#handoff-inputs)
- [Input Filters](#input-filters)
- [Conditional Handoffs](#conditional-handoffs)
- [Recommended Prompts](#recommended-prompts)

## Overview

Handoffs enable agents to delegate tasks to specialized agents. They appear as tools to the LLM (e.g., `transfer_to_billing_agent`). Use handoffs for:

- Customer support with specialized departments
- Multi-step workflows with domain experts
- Escalation paths to human agents

## Basic Handoffs

Simple agent-to-agent delegation:

```python
from agents import Agent

billing_agent = Agent(
    name="Billing Agent",
    instructions="Handle billing inquiries and payment issues",
)

refund_agent = Agent(
    name="Refund Agent",
    instructions="Process refund requests",
)

triage_agent = Agent(
    name="Triage Agent",
    instructions="Route customers to the right department",
    handoffs=[billing_agent, refund_agent],
)
```

## Customized Handoffs

Use `handoff()` for advanced configuration:

```python
from agents import Agent, handoff

billing_agent = Agent(name="Billing", instructions="Handle billing")

triage_agent = Agent(
    name="Triage",
    instructions="Route to appropriate agent",
    handoffs=[
        handoff(
            agent=billing_agent,
            tool_name_override="route_to_billing",
            tool_description_override="Transfer to billing for payment issues",
        )
    ],
)
```

## Handoff Inputs

Require structured data during handoffs:

```python
from pydantic import BaseModel
from agents import Agent, handoff, RunContextWrapper

class EscalationData(BaseModel):
    reason: str
    priority: str
    summary: str

async def on_escalate(
    ctx: RunContextWrapper[None],
    input_data: EscalationData
):
    print(f"Escalation: {input_data.reason}")
    print(f"Priority: {input_data.priority}")
    # Log to database, notify team, etc.

human_agent = Agent(name="Human Agent", instructions="Human support")

support_agent = Agent(
    name="Support",
    instructions="Help customers, escalate when needed",
    handoffs=[
        handoff(
            agent=human_agent,
            on_handoff=on_escalate,
            input_type=EscalationData,
        )
    ],
)
```

## Input Filters

Transform conversation history before passing to next agent:

```python
from agents import Agent, handoff
from agents.extensions.handoff_filters import remove_all_tools

# Remove tool calls from history (cleaner context)
specialist_agent = Agent(name="Specialist", instructions="Handle complex issues")

main_agent = Agent(
    name="Main",
    instructions="General assistance",
    handoffs=[
        handoff(
            agent=specialist_agent,
            input_filter=remove_all_tools,
        )
    ],
)
```

Custom filter:

```python
from agents.items import TResponseInputItem

def custom_filter(items: list[TResponseInputItem]) -> list[TResponseInputItem]:
    # Keep only last 5 messages
    return items[-5:]

handoff_obj = handoff(
    agent=target_agent,
    input_filter=custom_filter,
)
```

## Conditional Handoffs

Enable/disable handoffs dynamically:

```python
from agents import Agent, handoff, RunContextWrapper

premium_agent = Agent(name="Premium Support", instructions="VIP support")

def is_premium_user(
    ctx: RunContextWrapper[AppContext],
    agent: Agent
) -> bool:
    return ctx.context.user_tier == "premium"

support_agent = Agent(
    name="Support",
    instructions="Help customers",
    handoffs=[
        handoff(
            agent=premium_agent,
            is_enabled=is_premium_user,
        )
    ],
)
```

## Recommended Prompts

Use the built-in prompt prefix for better handoff behavior:

```python
from agents import Agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

triage_agent = Agent(
    name="Triage",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}

You are a customer service triage agent. Route customers to:
- Billing Agent: for payment and invoice issues
- Technical Support: for product problems
- Sales: for upgrade inquiries
""",
    handoffs=[billing_agent, tech_agent, sales_agent],
)
```

## Multi-Agent Workflow Example

Complete customer support system:

```python
from agents import Agent, handoff, Runner
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# Specialized agents
billing = Agent(
    name="Billing Agent",
    instructions="Handle billing inquiries. Be precise about amounts.",
)

technical = Agent(
    name="Technical Support",
    instructions="Solve technical issues. Ask for error messages.",
)

sales = Agent(
    name="Sales Agent",
    instructions="Handle upgrades and new purchases.",
)

# Triage agent routes to specialists
triage = Agent(
    name="Triage Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}

Route customers to the appropriate department:
- Billing: payments, invoices, refunds
- Technical: bugs, errors, how-to questions
- Sales: upgrades, new features, pricing
""",
    handoffs=[billing, technical, sales],
)

# Run the system
result = await Runner.run(
    triage,
    "I'm having trouble with my payment not going through"
)
# Result comes from billing agent after handoff
```
