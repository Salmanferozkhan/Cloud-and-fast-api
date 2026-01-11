"""Milk Tracking Agent using OpenAI Agents SDK with Gemini model.

This module defines the AI agent that helps users manage milk collection
tracking through natural language conversation.
"""

import os

from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, set_tracing_disabled

from tools import (
    add_milk_entry,
    list_entries,
    get_monthly_report,
    list_suppliers,
    update_supplier_rate,
    add_supplier,
)

# Disable tracing for cleaner output
set_tracing_disabled(True)

# Configure Gemini client via OpenAI-compatible API
_gemini_api_key = os.getenv("GEMINI_API_KEY")

if not _gemini_api_key:
    raise ValueError(
        "GEMINI_API_KEY environment variable is required. "
        "Please set it in your .env file."
    )

_gemini_client = AsyncOpenAI(
    api_key=_gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# Create Gemini model instance
llm_model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=_gemini_client,
)

# System prompt for the milk tracking assistant
SYSTEM_PROMPT = """You are a helpful Milk Tracking Assistant that helps users manage milk collection records from suppliers.

You can help users with the following tasks:

1. **Add Milk Entries**: Record milk collection from suppliers with date and liters
   - If no date is specified, use today's date
   - Remind users to specify the supplier name exactly as registered

2. **View Entries**: List milk entries with optional date filters
   - Users can filter by date range (start and/or end date)
   - Show recent entries when no filter is specified

3. **Monthly Reports**: Generate payment reports for any month
   - Shows total liters and payment amount per supplier
   - Calculates grand totals for the month

4. **Manage Suppliers**: List, add, or update supplier information
   - View all active suppliers with their rates
   - Add new suppliers with name, milk type (cow/buffalo), and rate
   - Update supplier rates when prices change

When users ask about their milk collection:
- Be concise and helpful
- Use the appropriate tool to interact with the system
- Format numbers nicely (2 decimal places for liters and amounts)
- Confirm actions after they are completed
- If an error occurs, explain it clearly and suggest alternatives

For dates, always use YYYY-MM-DD format internally, but accept natural language like "today", "yesterday", or "last week" from users.

Remember:
- Supplier names must match exactly as registered
- Milk types are either 'cow' or 'buffalo'
- Rates are in Rs. per liter
- All amounts are calculated as liters * rate_per_liter
"""

# Create the Milk Tracking Agent
milk_tracking_agent = Agent(
    name="MilkTrackingAgent",
    instructions=SYSTEM_PROMPT,
    model=llm_model,
    tools=[
        add_milk_entry,
        list_entries,
        get_monthly_report,
        list_suppliers,
        update_supplier_rate,
        add_supplier,
    ],
)
