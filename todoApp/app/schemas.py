"""API schemas for Todo endpoints."""
from sqlmodel import SQLModel, Field


class TodoBase(SQLModel):
    """Base schema with common fields."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool = Field(default=False)


class TodoCreate(TodoBase):
    """Schema for creating todos."""

    pass


class TodoUpdate(SQLModel):
    """Schema for updating todos - all fields optional."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    completed: bool | None = None


class TodoPublic(TodoBase):
    """Schema for API responses."""

    id: int

    model_config = {"from_attributes": True}
