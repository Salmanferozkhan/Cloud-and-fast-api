"""Database models."""
from sqlmodel import SQLModel, Field


class Todo(SQLModel, table=True):
    """Database table model for todos."""

    __tablename__ = "todos"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool = Field(default=False)
