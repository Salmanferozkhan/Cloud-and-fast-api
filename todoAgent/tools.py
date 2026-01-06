"""Tools for interacting with the Todo FastAPI backend."""
import httpx
from agents import function_tool

# Base URL for the Todo API
TODO_API_BASE_URL = "http://localhost:8080/api/v1/todos"


@function_tool
async def list_todos() -> str:
    """List all todos from the todo API.

    Returns a formatted list of all todos with their id, title, description, and status.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(TODO_API_BASE_URL)
        response.raise_for_status()
        todos = response.json()

        if not todos:
            return "No todos found. The todo list is empty."

        result = "Current todos:\n"
        for todo in todos:
            status = "completed" if todo["completed"] else "pending"
            desc = f" - {todo['description']}" if todo.get("description") else ""
            result += f"- [{todo['id']}] {todo['title']}{desc} ({status})\n"
        return result


@function_tool
async def get_todo(todo_id: int) -> str:
    """Get a specific todo by its ID.

    Args:
        todo_id: The unique identifier of the todo to retrieve.

    Returns details of the specified todo including title, description, and completion status.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TODO_API_BASE_URL}/{todo_id}")
        if response.status_code == 404:
            return f"Todo with ID {todo_id} not found."
        response.raise_for_status()
        todo = response.json()

        status = "completed" if todo["completed"] else "pending"
        desc = f"\nDescription: {todo['description']}" if todo.get("description") else ""
        return f"Todo #{todo['id']}: {todo['title']}{desc}\nStatus: {status}"


@function_tool
async def create_todo(title: str, description: str | None = None) -> str:
    """Create a new todo item.

    Args:
        title: The title of the todo (required, max 200 characters).
        description: Optional description of the todo (max 1000 characters).

    Returns confirmation with the created todo's details.
    """
    payload = {"title": title, "completed": False}
    if description:
        payload["description"] = description

    async with httpx.AsyncClient() as client:
        response = await client.post(TODO_API_BASE_URL, json=payload)
        response.raise_for_status()
        todo = response.json()

        desc = f" with description: {todo['description']}" if todo.get("description") else ""
        return f"Created todo #{todo['id']}: '{todo['title']}'{desc}"


@function_tool
async def update_todo(
    todo_id: int,
    title: str | None = None,
    description: str | None = None,
    completed: bool | None = None
) -> str:
    """Update an existing todo item.

    Args:
        todo_id: The ID of the todo to update.
        title: New title for the todo (optional).
        description: New description for the todo (optional).
        completed: Set to true to mark as completed, false for pending (optional).

    Returns confirmation with the updated todo's details.
    """
    payload = {}
    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description
    if completed is not None:
        payload["completed"] = completed

    if not payload:
        return "No updates provided. Please specify at least one field to update."

    async with httpx.AsyncClient() as client:
        response = await client.patch(f"{TODO_API_BASE_URL}/{todo_id}", json=payload)
        if response.status_code == 404:
            return f"Todo with ID {todo_id} not found."
        response.raise_for_status()
        todo = response.json()

        status = "completed" if todo["completed"] else "pending"
        return f"Updated todo #{todo['id']}: '{todo['title']}' - Status: {status}"


@function_tool
async def mark_todo_complete(todo_id: int) -> str:
    """Mark a todo as completed.

    Args:
        todo_id: The ID of the todo to mark as complete.

    Returns confirmation that the todo was marked complete.
    """
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{TODO_API_BASE_URL}/{todo_id}",
            json={"completed": True}
        )
        if response.status_code == 404:
            return f"Todo with ID {todo_id} not found."
        response.raise_for_status()
        todo = response.json()
        return f"Marked todo #{todo['id']} '{todo['title']}' as completed!"


@function_tool
async def mark_todo_incomplete(todo_id: int) -> str:
    """Mark a todo as incomplete/pending.

    Args:
        todo_id: The ID of the todo to mark as incomplete.

    Returns confirmation that the todo was marked incomplete.
    """
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{TODO_API_BASE_URL}/{todo_id}",
            json={"completed": False}
        )
        if response.status_code == 404:
            return f"Todo with ID {todo_id} not found."
        response.raise_for_status()
        todo = response.json()
        return f"Marked todo #{todo['id']} '{todo['title']}' as pending."


@function_tool
async def delete_todo(todo_id: int) -> str:
    """Delete a todo item permanently.

    Args:
        todo_id: The ID of the todo to delete.

    Returns confirmation that the todo was deleted.
    """
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{TODO_API_BASE_URL}/{todo_id}")
        if response.status_code == 404:
            return f"Todo with ID {todo_id} not found."
        response.raise_for_status()
        return f"Deleted todo #{todo_id} successfully."
