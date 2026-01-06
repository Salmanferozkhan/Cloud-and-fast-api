"""API routes for Todo endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_db
from app.models import Todo
from app.schemas import TodoCreate, TodoUpdate, TodoPublic

router = APIRouter(prefix="/todos", tags=["todos"])

# Type alias for dependency injection
DBDep = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=TodoPublic, status_code=status.HTTP_201_CREATED)
async def create_todo(todo_in: TodoCreate, db: DBDep) -> Todo:
    """Create a new todo."""
    todo = Todo.model_validate(todo_in)
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    return todo


@router.get("", response_model=list[TodoPublic])
async def list_todos(db: DBDep, skip: int = 0, limit: int = 100) -> list[Todo]:
    """List all todos with pagination."""
    result = await db.execute(select(Todo).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{todo_id}", response_model=TodoPublic)
async def get_todo(todo_id: int, db: DBDep) -> Todo:
    """Get a single todo by ID."""
    todo = await db.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.patch("/{todo_id}", response_model=TodoPublic)
async def update_todo(todo_id: int, todo_in: TodoUpdate, db: DBDep) -> Todo:
    """Update a todo by ID."""
    todo = await db.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    update_data = todo_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(todo, key, value)

    await db.commit()
    await db.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: int, db: DBDep) -> None:
    """Delete a todo by ID."""
    todo = await db.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    await db.delete(todo)
    await db.commit()
