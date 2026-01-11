"""Database models for the Milk Tracking API."""

import datetime as dt
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> dt.datetime:
    """Return current UTC time as naive datetime (for PostgreSQL compatibility)."""
    return dt.datetime.utcnow()


class User(SQLModel, table=True):
    """User model for authentication.

    Attributes:
        id: Primary key, auto-generated.
        email: User's email address, unique and indexed.
        hashed_password: Argon2-hashed password.
        created_at: Timestamp when user was created.
    """

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: dt.datetime = Field(default_factory=utc_now)


class MilkType(str, Enum):
    """Enum for types of milk supplied.

    Attributes:
        COW: Cow milk.
        BUFFALO: Buffalo milk.
    """

    COW = "cow"
    BUFFALO = "buffalo"


class MilkEntry(SQLModel, table=True):
    """MilkEntry model for daily milk collection records.

    Attributes:
        id: Primary key, auto-generated.
        date: Date of the milk collection.
        supplier_id: Foreign key to the supplier.
        liters: Amount of milk collected in liters (must be positive).
        created_at: Timestamp when entry was created.
        supplier: Relationship to the Supplier model.
    """

    __tablename__ = "milk_entries"

    id: int | None = Field(default=None, primary_key=True)
    date: dt.date = Field(..., index=True)
    supplier_id: int = Field(..., foreign_key="suppliers.id", index=True)
    liters: float = Field(..., gt=0)
    created_at: dt.datetime = Field(default_factory=utc_now)

    # Relationship to supplier
    supplier: Optional["Supplier"] = Relationship(back_populates="entries")


class Supplier(SQLModel, table=True):
    """Supplier model for milk suppliers.

    Attributes:
        id: Primary key, auto-generated.
        name: Supplier's name, unique.
        milk_type: Type of milk supplied (cow or buffalo).
        rate_per_liter: Price per liter of milk.
        is_active: Whether the supplier is active (soft delete flag).
        created_at: Timestamp when supplier was created.
        entries: List of milk entries from this supplier.
    """

    __tablename__ = "suppliers"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(..., min_length=1, max_length=100, unique=True, index=True)
    milk_type: MilkType
    rate_per_liter: float = Field(..., gt=0)
    is_active: bool = Field(default=True)
    created_at: dt.datetime = Field(default_factory=utc_now)

    # Relationship to milk entries
    entries: List["MilkEntry"] = Relationship(back_populates="supplier")
