"""Todo Agent using OpenAI Agents SDK with Gemini via OpenAI-compatible API.

Includes fallback to DeepSeek API if Gemini quota is exhausted.
"""
import os
from collections.abc import AsyncIterator

from openai import AsyncOpenAI, RateLimitError, APIStatusError
from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled, function_tool, ModelSettings
from agents.models.interface import Model, ModelTracing
from agents.agent_output import AgentOutputSchemaBase
from agents.handoffs import Handoff
from agents.items import ModelResponse, TResponseInputItem, TResponseStreamEvent
from agents.tool import Tool
set_tracing_disabled(True)
from tools import (
    list_todos,
    get_todo,
    create_todo,
    update_todo,
    mark_todo_complete,
    mark_todo_incomplete,
    delete_todo,
)


# Configure Gemini client
_gemini_api_key = os.getenv("GEMINI_API_KEY")
_gemini_client = None
if _gemini_api_key:
    _gemini_client = AsyncOpenAI(
        api_key=_gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

# Configure DeepSeek client (fallback)
_deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
_deepseek_client = None
if _deepseek_api_key:
    _deepseek_client = AsyncOpenAI(
        api_key=_deepseek_api_key,
        base_url="https://api.deepseek.com",
    )


class FallbackModel(Model):
    """Model wrapper that falls back to DeepSeek if Gemini quota is exhausted."""

    def __init__(self, primary_model: Model, fallback_model: Model):
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self._use_fallback = False

    async def get_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt=None,
    ) -> ModelResponse:
        """Try primary model, fall back to secondary on rate limit errors."""
        if self._use_fallback and self.fallback_model:
            print("[Fallback] Using DeepSeek API")
            return await self.fallback_model.get_response(
                system_instructions, input, model_settings, tools,
                output_schema, handoffs, tracing,
                previous_response_id=previous_response_id,
                conversation_id=conversation_id,
                prompt=prompt,
            )

        try:
            return await self.primary_model.get_response(
                system_instructions, input, model_settings, tools,
                output_schema, handoffs, tracing,
                previous_response_id=previous_response_id,
                conversation_id=conversation_id,
                prompt=prompt,
            )
        except (RateLimitError, APIStatusError) as e:
            # Check for quota/rate limit errors (429, 503, or quota-related messages)
            is_quota_error = (
                isinstance(e, RateLimitError) or
                (isinstance(e, APIStatusError) and e.status_code in (429, 503)) or
                "quota" in str(e).lower() or
                "rate" in str(e).lower()
            )

            if is_quota_error and self.fallback_model:
                print(f"[Fallback] Gemini API exhausted ({e}), switching to DeepSeek")
                self._use_fallback = True
                return await self.fallback_model.get_response(
                    system_instructions, input, model_settings, tools,
                    output_schema, handoffs, tracing,
                    previous_response_id=previous_response_id,
                    conversation_id=conversation_id,
                    prompt=prompt,
                )
            raise

    def stream_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt=None,
    ) -> AsyncIterator[TResponseStreamEvent]:
        """Try primary model, fall back to secondary on rate limit errors."""
        return self._stream_response_impl(
            system_instructions, input, model_settings, tools,
            output_schema, handoffs, tracing,
            previous_response_id=previous_response_id,
            conversation_id=conversation_id,
            prompt=prompt,
        )

    async def _stream_response_impl(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt=None,
    ) -> AsyncIterator[TResponseStreamEvent]:
        if self._use_fallback and self.fallback_model:
            async for chunk in self.fallback_model.stream_response(
                system_instructions, input, model_settings, tools,
                output_schema, handoffs, tracing,
                previous_response_id=previous_response_id,
                conversation_id=conversation_id,
                prompt=prompt,
            ):
                yield chunk
            return

        try:
            async for chunk in self.primary_model.stream_response(
                system_instructions, input, model_settings, tools,
                output_schema, handoffs, tracing,
                previous_response_id=previous_response_id,
                conversation_id=conversation_id,
                prompt=prompt,
            ):
                yield chunk
        except (RateLimitError, APIStatusError) as e:
            is_quota_error = (
                isinstance(e, RateLimitError) or
                (isinstance(e, APIStatusError) and e.status_code in (429, 503)) or
                "quota" in str(e).lower() or
                "rate" in str(e).lower()
            )

            if is_quota_error and self.fallback_model:
                print(f"[Fallback] Gemini API exhausted ({e}), switching to DeepSeek")
                self._use_fallback = True
                async for chunk in self.fallback_model.stream_response(
                    system_instructions, input, model_settings, tools,
                    output_schema, handoffs, tracing,
                    previous_response_id=previous_response_id,
                    conversation_id=conversation_id,
                    prompt=prompt,
                ):
                    yield chunk
            else:
                raise


# Create primary (Gemini) and fallback (DeepSeek) models
_gemini_model = None
if _gemini_client:
    _gemini_model = OpenAIChatCompletionsModel(model="gemini-2.5-flash", openai_client=_gemini_client)

_deepseek_model = None
if _deepseek_client:
    _deepseek_model = OpenAIChatCompletionsModel(model="deepseek-chat", openai_client=_deepseek_client)

# Use fallback wrapper if both are available, otherwise use whichever is available
if _gemini_model and _deepseek_model:
    llm_model = FallbackModel(_gemini_model, _deepseek_model)
elif _gemini_model:
    llm_model = _gemini_model
elif _deepseek_model:
    llm_model = _deepseek_model
else:
    raise ValueError("No API keys configured. Set GEMINI_API_KEY or DEEPSEEK_API_KEY.")
# Todo Agent with Gemini primary and DeepSeek fallback
todo_agent = Agent(
    name="TodoAgent",
    instructions="""You are a helpful Todo Assistant that helps users manage their tasks.

You can:
- List all todos
- Get details of a specific todo by ID
- Create new todos with a title and optional description
- Update existing todos (title, description, or completion status)
- Mark todos as complete or incomplete
- Delete todos

When users ask about their tasks, always start by listing current todos to give context.
Be concise and helpful. When creating todos, confirm what was created.
When marking tasks complete, be encouraging!

Always use the appropriate tool to interact with the todo system.
If an error occurs, explain it clearly and suggest alternatives.""",
    model=llm_model,
    tools=[
        list_todos,
        get_todo,
        create_todo,
        update_todo,
        mark_todo_complete,
        mark_todo_incomplete,
        delete_todo,
    ],
)
