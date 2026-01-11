"""Suppliers router for managing milk suppliers."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth import CurrentUser
from app.database import get_session
from app.models import Supplier
from app.schemas import SupplierCreate, SupplierResponse, SupplierUpdate

router = APIRouter(tags=["suppliers"])

# Type alias for database session dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new supplier",
    description="Create a new milk supplier with name, milk type, and rate per liter.",
)
async def create_supplier(
    supplier_data: SupplierCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Supplier:
    """Create a new supplier.

    Args:
        supplier_data: Supplier creation data (name, milk_type, rate_per_liter).
        session: Database session.
        current_user: The authenticated user.

    Returns:
        Supplier: The created supplier.

    Raises:
        HTTPException: 400 if supplier name already exists.
    """
    # Check if supplier name already exists
    statement = select(Supplier).where(Supplier.name == supplier_data.name)
    result = await session.execute(statement)
    existing_supplier = result.scalar_one_or_none()

    if existing_supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplier with this name already exists",
        )

    # Create new supplier
    supplier = Supplier(
        name=supplier_data.name,
        milk_type=supplier_data.milk_type,
        rate_per_liter=supplier_data.rate_per_liter,
    )

    session.add(supplier)
    await session.commit()
    await session.refresh(supplier)

    return supplier


@router.get(
    "",
    response_model=list[SupplierResponse],
    summary="List all active suppliers",
    description="Get a list of all active suppliers.",
)
async def list_suppliers(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[Supplier]:
    """List all active suppliers.

    Args:
        session: Database session.
        current_user: The authenticated user.

    Returns:
        list[Supplier]: List of active suppliers.
    """
    statement = select(Supplier).where(Supplier.is_active == True)  # noqa: E712
    result = await session.execute(statement)
    suppliers = result.scalars().all()

    return list(suppliers)


# Static path routes must be defined BEFORE dynamic path routes
@router.get(
    "/by-name/{name:path}",
    response_model=SupplierResponse,
    summary="Get supplier by name",
    description="Get a specific supplier by their name.",
)
async def get_supplier_by_name(
    name: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> Supplier:
    """Get a supplier by name.

    Args:
        name: The supplier's name.
        session: Database session.
        current_user: The authenticated user.

    Returns:
        Supplier: The requested supplier.

    Raises:
        HTTPException: 404 if supplier not found or inactive.
    """
    statement = select(Supplier).where(
        Supplier.name == name,
        Supplier.is_active == True,  # noqa: E712
    )
    result = await session.execute(statement)
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    return supplier


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Get supplier by ID",
    description="Get a specific supplier by their ID.",
)
async def get_supplier_by_id(
    supplier_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> Supplier:
    """Get a supplier by ID.

    Args:
        supplier_id: The supplier's ID.
        session: Database session.
        current_user: The authenticated user.

    Returns:
        Supplier: The requested supplier.

    Raises:
        HTTPException: 404 if supplier not found or inactive.
    """
    statement = select(Supplier).where(
        Supplier.id == supplier_id,
        Supplier.is_active == True,  # noqa: E712
    )
    result = await session.execute(statement)
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    return supplier


@router.patch(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Update supplier",
    description="Update a supplier's information. All fields are optional.",
)
async def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Supplier:
    """Update a supplier.

    Args:
        supplier_id: The supplier's ID.
        supplier_data: Supplier update data (all fields optional).
        session: Database session.
        current_user: The authenticated user.

    Returns:
        Supplier: The updated supplier.

    Raises:
        HTTPException: 404 if supplier not found.
        HTTPException: 400 if new name already exists.
    """
    # Get supplier (including inactive ones for reactivation)
    statement = select(Supplier).where(Supplier.id == supplier_id)
    result = await session.execute(statement)
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check for duplicate name if name is being updated
    if supplier_data.name is not None and supplier_data.name != supplier.name:
        name_check = select(Supplier).where(Supplier.name == supplier_data.name)
        name_result = await session.execute(name_check)
        existing = name_result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplier with this name already exists",
            )

    # Update only provided fields
    update_data = supplier_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    session.add(supplier)
    await session.commit()
    await session.refresh(supplier)

    return supplier


@router.delete(
    "/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete supplier",
    description="Soft-delete a supplier by setting is_active to False.",
)
async def delete_supplier(
    supplier_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> None:
    """Soft-delete a supplier.

    Args:
        supplier_id: The supplier's ID.
        session: Database session.
        current_user: The authenticated user.

    Raises:
        HTTPException: 404 if supplier not found or already inactive.
    """
    statement = select(Supplier).where(
        Supplier.id == supplier_id,
        Supplier.is_active == True,  # noqa: E712
    )
    result = await session.execute(statement)
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Soft delete
    supplier.is_active = False
    session.add(supplier)
    await session.commit()
