"""Pydantic schemas for request/response validation."""

import datetime as dt

from pydantic import BaseModel, EmailStr, Field

from app.models import MilkType


class UserCreate(BaseModel):
    """Schema for user registration request.

    Attributes:
        email: Valid email address.
        password: Plain text password.
    """

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (excludes sensitive data).

    Attributes:
        id: User's unique identifier.
        email: User's email address.
        created_at: Timestamp when user was created.
    """

    id: int
    email: str
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT token response.

    Attributes:
        access_token: The JWT access token.
        token_type: Token type, always "bearer".
    """

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data.

    Attributes:
        email: User's email from the token subject.
    """

    email: str | None = None


# Supplier Schemas


class SupplierCreate(BaseModel):
    """Schema for creating a new supplier.

    Attributes:
        name: Supplier's name (1-100 characters).
        milk_type: Type of milk (cow or buffalo).
        rate_per_liter: Price per liter (must be positive).
    """

    name: str = Field(..., min_length=1, max_length=100)
    milk_type: MilkType
    rate_per_liter: float = Field(..., gt=0)


class SupplierUpdate(BaseModel):
    """Schema for updating an existing supplier.

    All fields are optional - only provided fields will be updated.

    Attributes:
        name: Supplier's name (1-100 characters).
        milk_type: Type of milk (cow or buffalo).
        rate_per_liter: Price per liter (must be positive).
        is_active: Whether the supplier is active.
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    milk_type: MilkType | None = None
    rate_per_liter: float | None = Field(default=None, gt=0)
    is_active: bool | None = None


class SupplierResponse(BaseModel):
    """Schema for supplier response.

    Attributes:
        id: Supplier's unique identifier.
        name: Supplier's name.
        milk_type: Type of milk supplied.
        rate_per_liter: Price per liter.
        is_active: Whether the supplier is active.
        created_at: Timestamp when supplier was created.
    """

    id: int
    name: str
    milk_type: MilkType
    rate_per_liter: float
    is_active: bool
    created_at: dt.datetime

    model_config = {"from_attributes": True}


# MilkEntry Schemas


class EntryCreate(BaseModel):
    """Schema for creating a new milk entry by supplier ID.

    Attributes:
        date: Date of the milk collection.
        supplier_id: ID of the supplier.
        liters: Amount of milk in liters (must be positive).
    """

    date: dt.date
    supplier_id: int
    liters: float = Field(..., gt=0)


class EntryCreateByName(BaseModel):
    """Schema for creating a new milk entry by supplier name.

    Attributes:
        date: Date of the milk collection.
        supplier_name: Name of the supplier.
        liters: Amount of milk in liters (must be positive).
    """

    date: dt.date
    supplier_name: str = Field(..., min_length=1, max_length=100)
    liters: float = Field(..., gt=0)


class EntryUpdate(BaseModel):
    """Schema for updating an existing milk entry.

    All fields are optional - only provided fields will be updated.

    Attributes:
        date: Date of the milk collection.
        supplier_id: ID of the supplier.
        liters: Amount of milk in liters (must be positive).
    """

    date: dt.date | None = None
    supplier_id: int | None = None
    liters: float | None = Field(default=None, gt=0)


class EntryResponse(BaseModel):
    """Schema for milk entry response.

    Attributes:
        id: Entry's unique identifier.
        date: Date of the milk collection.
        supplier_id: ID of the supplier.
        liters: Amount of milk in liters.
        created_at: Timestamp when entry was created.
        supplier: Nested supplier information.
    """

    id: int
    date: dt.date
    supplier_id: int
    liters: float
    created_at: dt.datetime
    supplier: SupplierResponse

    model_config = {"from_attributes": True}


# Report Schemas


class SupplierReport(BaseModel):
    """Schema for individual supplier report data.

    Attributes:
        supplier_id: The supplier's unique identifier.
        supplier_name: The supplier's name.
        milk_type: Type of milk supplied (cow or buffalo).
        rate_per_liter: Price per liter of milk.
        total_liters: Total liters of milk collected from this supplier.
        total_amount: Total payment amount (total_liters * rate_per_liter).
    """

    supplier_id: int
    supplier_name: str
    milk_type: MilkType
    rate_per_liter: float
    total_liters: float
    total_amount: float  # total_liters * rate_per_liter


class MonthlyReport(BaseModel):
    """Schema for monthly payment report.

    Attributes:
        year: The report year.
        month: The report month (1-12).
        suppliers: List of supplier reports with totals.
        grand_total_liters: Sum of all suppliers' total liters.
        grand_total_amount: Sum of all suppliers' total amounts.
    """

    year: int
    month: int = Field(..., ge=1, le=12)
    suppliers: list[SupplierReport]
    grand_total_liters: float
    grand_total_amount: float
