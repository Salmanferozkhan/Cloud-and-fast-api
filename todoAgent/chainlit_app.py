"""Chainlit UI for Todo Agent with streaming support.

Run with: chainlit run chainlit_app.py -w
"""
import json

from dotenv import find_dotenv, load_dotenv

# Load environment variables BEFORE importing agent (which needs API keys)
load_dotenv(find_dotenv())

import chainlit as cl
from agents import Runner

from agent import todo_agent


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session."""
    cl.user_session.set("history", [])
    await cl.Message(
        content="Hello! I'm your Todo Assistant. I can help you manage your tasks.\n\n"
        "You can ask me to:\n"
        "- List all your todos\n"
        "- Create new todos\n"
        "- Update or delete todos\n"
        "- Mark todos as complete or incomplete\n\n"
        "What would you like to do?"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages with streaming response."""
    # Get conversation history
    history = cl.user_session.get("history", [])

    # Build input with history for context
    input_messages = []
    for h in history:
        input_messages.append({"role": "user", "content": h["user"]})
        input_messages.append({"role": "assistant", "content": h["assistant"]})
    input_messages.append({"role": "user", "content": message.content})

    # Create message placeholder for streaming
    msg = cl.Message(content="")
    await msg.send()

    # Run agent with streaming
    result = Runner.run_streamed(todo_agent, input_messages)

    full_response = ""
    current_step = None
    tool_calls = {}  # Track tool calls by ID

    # Stream the response
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            # Handle text delta events
            if hasattr(event.data, "delta"):
                delta = event.data.delta
                if delta:
                    full_response += delta
                    await msg.stream_token(delta)

        elif event.type == "run_item_stream_event":
            # Handle tool calls and results
            item = event.item
            item_type = getattr(item, "type", None)

            if item_type == "tool_call_item":
                # Tool is being called
                tool_name = getattr(item, "name", "tool")
                tool_call_id = getattr(item, "call_id", id(item))
                raw_args = getattr(item, "arguments", "{}")

                # Parse arguments for display
                try:
                    args = json.loads(raw_args) if raw_args else {}
                    args_display = json.dumps(args, indent=2)
                except (json.JSONDecodeError, TypeError):
                    args_display = str(raw_args)

                # Create a step for this tool call
                step = cl.Step(name=tool_name, type="tool")
                step.input = args_display
                await step.send()
                tool_calls[tool_call_id] = step

            elif item_type == "tool_call_output_item":
                # Tool result received
                tool_call_id = getattr(item, "call_id", None)
                output = getattr(item, "output", "")

                # Find and update the matching step
                if tool_call_id and tool_call_id in tool_calls:
                    step = tool_calls[tool_call_id]
                    step.output = output
                    await step.update()

    # Finalize the message
    await msg.update()

    # Get final output if streaming didn't capture it
    if not full_response:
        final_result = await result.wait()
        if final_result.final_output:
            full_response = final_result.final_output
            await msg.stream_token(full_response)
            await msg.update()

    # Update history (keep last 10 turns to avoid context overflow)
    history.append({"user": message.content, "assistant": full_response or msg.content})
    if len(history) > 10:
        history = history[-10:]
    cl.user_session.set("history", history)


@cl.on_chat_end
async def on_chat_end():
    """Clean up when chat session ends."""
    print("Chat session ended")
