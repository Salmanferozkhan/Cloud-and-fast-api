"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    """Base item schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    price: float = Field(..., gt=0)


class ItemCreate(ItemBase):
    """Schema for creating items."""
    pass


class ItemResponse(ItemBase):
    """Schema for item responses."""
    id: int

    model_config = {"from_attributes": True}
