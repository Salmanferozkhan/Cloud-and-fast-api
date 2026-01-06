# Common Patterns Reference

## Table of Contents
- [Customer Support System](#customer-support-system)
- [Research Assistant](#research-assistant)
- [Data Processing Pipeline](#data-processing-pipeline)
- [Code Assistant](#code-assistant)
- [RAG Pattern](#rag-pattern)
- [Human-in-the-Loop](#human-in-the-loop)

## Customer Support System

Multi-agent system with triage and specialists:

```python
from agents import Agent, handoff, Runner, function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions.session import SQLiteSession

# Tools for specialists
@function_tool
def lookup_order(order_id: str) -> str:
    """Look up order details."""
    return f"Order {order_id}: Shipped, arriving tomorrow"

@function_tool
def process_refund(order_id: str, reason: str) -> str:
    """Process a refund request."""
    return f"Refund initiated for {order_id}. Reason: {reason}"

@function_tool
def check_inventory(product_id: str) -> str:
    """Check product inventory."""
    return f"Product {product_id}: 50 units in stock"

# Specialist agents
billing_agent = Agent(
    name="Billing Agent",
    instructions="""Handle billing inquiries:
    - Payment issues
    - Invoice questions
    - Subscription management
    Be precise about amounts and dates.""",
    tools=[lookup_order],
)

refund_agent = Agent(
    name="Refund Agent",
    instructions="""Process refund requests:
    - Verify order exists
    - Confirm refund eligibility
    - Process the refund""",
    tools=[lookup_order, process_refund],
)

sales_agent = Agent(
    name="Sales Agent",
    instructions="""Help with sales inquiries:
    - Product availability
    - Pricing questions
    - New orders""",
    tools=[check_inventory],
)

# Triage agent
triage_agent = Agent(
    name="Support Triage",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}

You are the first point of contact for customer support.
Route customers to the appropriate specialist:

- Billing Agent: payments, invoices, subscriptions
- Refund Agent: returns, refunds, exchanges
- Sales Agent: product info, pricing, new orders

Ask clarifying questions if the intent is unclear.""",
    handoffs=[billing_agent, refund_agent, sales_agent],
)

# Run support system
async def handle_support(user_id: str, message: str) -> str:
    session = SQLiteSession(user_id, "support.db")
    result = await Runner.run(triage_agent, message, session=session)
    return result.final_output
```

## Research Assistant

Agent that gathers and synthesizes information:

```python
from agents import Agent, Runner, function_tool
from pydantic import BaseModel

class ResearchReport(BaseModel):
    topic: str
    summary: str
    key_findings: list[str]
    sources: list[str]

@function_tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Implement web search
    return f"Search results for: {query}"

@function_tool
def search_academic(query: str) -> str:
    """Search academic papers."""
    # Implement academic search
    return f"Academic papers about: {query}"

@function_tool
def summarize_url(url: str) -> str:
    """Summarize content from a URL."""
    # Implement URL summarization
    return f"Summary of {url}"

research_agent = Agent(
    name="Research Assistant",
    instructions="""You are a thorough research assistant.

    When given a topic:
    1. Search multiple sources (web, academic)
    2. Gather relevant information
    3. Synthesize findings into a coherent report
    4. Cite your sources

    Be objective and note any conflicting information.""",
    tools=[search_web, search_academic, summarize_url],
    output_type=ResearchReport,
)

async def research(topic: str) -> ResearchReport:
    result = await Runner.run(research_agent, f"Research: {topic}")
    return result.final_output
```

## Data Processing Pipeline

Sequential agents for data transformation:

```python
from agents import Agent, Runner, function_tool
from pydantic import BaseModel

class ProcessedData(BaseModel):
    original_count: int
    cleaned_count: int
    transformations: list[str]
    output_path: str

@function_tool
def read_csv(path: str) -> str:
    """Read a CSV file."""
    return f"Read 1000 rows from {path}"

@function_tool
def clean_data(data: str) -> str:
    """Clean and validate data."""
    return "Cleaned: removed 50 invalid rows, standardized formats"

@function_tool
def transform_data(data: str, operations: str) -> str:
    """Apply transformations to data."""
    return f"Applied transformations: {operations}"

@function_tool
def write_csv(data: str, path: str) -> str:
    """Write data to CSV."""
    return f"Wrote 950 rows to {path}"

data_agent = Agent(
    name="Data Processor",
    instructions="""Process data files through these steps:
    1. Read the input file
    2. Clean and validate the data
    3. Apply requested transformations
    4. Write to output file

    Report what was done at each step.""",
    tools=[read_csv, clean_data, transform_data, write_csv],
    output_type=ProcessedData,
)

async def process_data(input_file: str, output_file: str, transforms: str) -> ProcessedData:
    prompt = f"""Process {input_file}:
    - Apply transformations: {transforms}
    - Output to: {output_file}"""
    result = await Runner.run(data_agent, prompt)
    return result.final_output
```

## Code Assistant

Multi-agent code helper:

```python
from agents import Agent, handoff, Runner, function_tool

@function_tool
def read_file(path: str) -> str:
    """Read a source code file."""
    with open(path) as f:
        return f.read()

@function_tool
def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    with open(path, 'w') as f:
        f.write(content)
    return f"Wrote {len(content)} chars to {path}"

@function_tool
def run_tests(path: str) -> str:
    """Run tests for a file."""
    return "All 10 tests passed"

@function_tool
def lint_code(code: str) -> str:
    """Check code for style issues."""
    return "No linting issues found"

# Specialist agents
code_writer = Agent(
    name="Code Writer",
    instructions="""Write clean, well-documented code.
    - Follow best practices
    - Add docstrings and comments
    - Handle edge cases""",
    tools=[read_file, write_file],
)

code_reviewer = Agent(
    name="Code Reviewer",
    instructions="""Review code for:
    - Bugs and edge cases
    - Performance issues
    - Style and readability
    - Security concerns
    Provide specific, actionable feedback.""",
    tools=[read_file, lint_code],
)

test_writer = Agent(
    name="Test Writer",
    instructions="""Write comprehensive tests:
    - Unit tests for each function
    - Edge case coverage
    - Integration tests where needed""",
    tools=[read_file, write_file, run_tests],
)

# Coordinator
code_assistant = Agent(
    name="Code Assistant",
    instructions="""Help with coding tasks:
    - Writing new code -> Code Writer
    - Reviewing code -> Code Reviewer
    - Writing tests -> Test Writer

    Understand the request and route appropriately.""",
    handoffs=[code_writer, code_reviewer, test_writer],
)
```

## RAG Pattern

Retrieval-Augmented Generation:

```python
from agents import Agent, Runner, function_tool
from pydantic import BaseModel

class Answer(BaseModel):
    answer: str
    confidence: float
    sources: list[str]

@function_tool
def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for relevant documents."""
    # Implement vector search
    return """
    [Doc 1] Company policy on returns: 30-day return window...
    [Doc 2] Return exceptions: Electronics have 15-day window...
    """

@function_tool
def get_document(doc_id: str) -> str:
    """Retrieve a specific document by ID."""
    return f"Full content of document {doc_id}..."

rag_agent = Agent(
    name="Knowledge Assistant",
    instructions="""Answer questions using the knowledge base.

    Process:
    1. Search for relevant documents
    2. Read the most relevant ones
    3. Synthesize an answer from the sources
    4. Cite which documents you used

    If information isn't in the knowledge base, say so.""",
    tools=[search_knowledge_base, get_document],
    output_type=Answer,
)

async def ask(question: str) -> Answer:
    result = await Runner.run(rag_agent, question)
    return result.final_output
```

## Human-in-the-Loop

Escalation to human agents:

```python
from agents import Agent, handoff, Runner, function_tool
from pydantic import BaseModel

class EscalationRequest(BaseModel):
    reason: str
    priority: str
    context_summary: str

@function_tool
def create_ticket(
    subject: str,
    description: str,
    priority: str
) -> str:
    """Create a support ticket for human review."""
    return f"Created ticket #12345: {subject} (Priority: {priority})"

@function_tool
def notify_human(message: str, channel: str) -> str:
    """Send notification to human agents."""
    return f"Notified {channel}: {message}"

# Human handoff placeholder
human_agent = Agent(
    name="Human Agent",
    instructions="This conversation has been escalated to a human agent.",
)

async def on_escalate(ctx, data: EscalationRequest):
    # Create ticket and notify
    await ctx.run_tool(create_ticket, {
        "subject": data.reason,
        "description": data.context_summary,
        "priority": data.priority,
    })
    await ctx.run_tool(notify_human, {
        "message": f"New escalation: {data.reason}",
        "channel": "support-team",
    })

support_agent = Agent(
    name="Support Agent",
    instructions="""Help customers with their issues.

    Escalate to a human when:
    - Customer explicitly requests a human
    - Issue requires account-level access
    - Situation is emotionally charged
    - You cannot resolve after 3 attempts""",
    handoffs=[
        handoff(
            agent=human_agent,
            on_handoff=on_escalate,
            input_type=EscalationRequest,
            tool_description_override="Escalate to a human agent",
        )
    ],
)
```
