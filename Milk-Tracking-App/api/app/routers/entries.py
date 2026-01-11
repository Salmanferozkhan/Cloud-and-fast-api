"""Entries router for managing milk collection entries."""

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.auth import CurrentUser
from app.database import get_session
from app.models import MilkEntry, Supplier
from app.schemas import EntryCreate, EntryCreateByName, EntryResponse, EntryUpdate

router = APIRouter(tags=["entries"])

# Type alias for database session dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_supplier_by_id(session: AsyncSession, supplier_id: int) -> Supplier | None:
    """Get an active supplier by ID.

    Args:
        session: Database session.
        supplier_id: The supplier's ID.

    Returns:
        Supplier if found and active, None otherwise.
    """
    statement = select(Supplier).where(
        Supplier.id == supplier_id,
        Supplier.is_active == True,  # noqa: E712
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_supplier_by_name(session: AsyncSession, name: str) -> Supplier | None:
    """Get an active supplier by name.

    Args:
        session: Database session.
        name: The supplier's name.

    Returns:
        Supplier if found and active, None otherwise.
    """
    statement = select(Supplier).where(
        Supplier.name == name,
        Supplier.is_active == True,  # noqa: E712
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


@router.post(
    "",
    response_model=EntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new milk entry by supplier ID",
    description="Create a new milk collection entry with date, supplier ID, and liters.",
)
async def create_entry(
    entry_data: EntryCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> MilkEntry:
    """Create a new milk entry by supplier ID.

    Args:
        entry_data: Entry creation data (date, supplier_id, liters).
        session: Database session.
        current_user: The authenticated user.

    Returns:
        MilkEntry: The created entry with supplier information.

    Raises:
        HTTPException: 404 if supplier not found.
    """
    # Verify supplier exists and is active
    supplier = await get_supplier_by_id(session, entry_data.supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Create new entry
    entry = MilkEntry(
        date=entry_data.date,
        supplier_id=entry_data.supplier_id,
        liters=entry_data.liters,
    )

    session.add(entry)
    await session.commit()
    await session.refresh(entry)

    # Reload with supplier relationship
    statement = (
        select(MilkEntry)
        .where(MilkEntry.id == entry.id)
        .options(selectinload(MilkEntry.supplier))
    )
    result = await session.execute(statement)
    return result.scalar_one()


@router.post(
    "/by-name",
    response_model=EntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new milk entry by supplier name",
    description="Create a new milk collection entry with date, supplier name, and liters.",
)
async def create_entry_by_name(
    entry_data: EntryCreateByName,
    session: SessionDep,
    current_user: CurrentUser,
) -> MilkEntry:
    """Create a new milk entry by supplier name.

    Args:
        entry_data: Entry creation data (date, supplier_name, liters).
        session: Database session.
        current_user: The authenticated user.

    Returns:
        MilkEntry: The created entry with supplier information.

    Raises:
        HTTPException: 404 if supplier not found.
    """
    # Find supplier by name
    supplier = await get_supplier_by_name(session, entry_data.supplier_name)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Create new entry
    entry = MilkEntry(
        date=entry_data.date,
        supplier_id=supplier.id,
        liters=entry_data.liters,
    )

    session.add(entry)
    await session.commit()
    await session.refresh(entry)

    # Reload with supplier relationship
    statement = (
        select(MilkEntry)
        .where(MilkEntry.id == entry.id)
        .options(selectinload(MilkEntry.supplier))
    )
    result = await session.execute(statement)
    return result.scalar_one()


@router.get(
    "",
    response_model=list[EntryResponse],
    summary="List all milk entries",
    description="Get a list of all milk entries with optional date filters.",
)
async def list_entries(
    session: SessionDep,
    current_user: CurrentUser,
    start_date: dt.date | None = Query(default=None, description="Filter entries from this date"),
    end_date: dt.date | None = Query(default=None, description="Filter entries until this date"),
) -> list[MilkEntry]:
    """List all milk entries with optional date filters.

    Args:
        session: Database session.
        current_user: The authenticated user.
        start_date: Optional start date filter (inclusive).
        end_date: Optional end date filter (inclusive).

    Returns:
        list[MilkEntry]: List of milk entries.
    """
    statement = select(MilkEntry).options(selectinload(MilkEntry.supplier))

    if start_date:
        statement = statement.where(MilkEntry.date >= start_date)
    if end_date:
        statement = statement.where(MilkEntry.date <= end_date)

    statement = statement.order_by(MilkEntry.date.desc())

    result = await session.execute(statement)
    entries = result.scalars().all()

    return list(entries)


@router.get(
    "/{entry_id}",
    response_model=EntryResponse,
    summary="Get milk entry by ID",
    description="Get a specific milk entry by its ID.",
)
async def get_entry_by_id(
    entry_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> MilkEntry:
    """Get a milk entry by ID.

    Args:
        entry_id: The entry's ID.
        session: Database session.
        current_user: The authenticated user.

    Returns:
        MilkEntry: The requested entry with supplier information.

    Raises:
        HTTPException: 404 if entry not found.
    """
    statement = (
        select(MilkEntry)
        .where(MilkEntry.id == entry_id)
        .options(selectinload(MilkEntry.supplier))
    )
    result = await session.execute(statement)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    return entry


@router.patch(
    "/{entry_id}",
    response_model=EntryResponse,
    summary="Update milk entry",
    description="Update a milk entry's information. All fields are optional.",
)
async def update_entry(
    entry_id: int,
    entry_data: EntryUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> MilkEntry:
    """Update a milk entry.

    Args:
        entry_id: The entry's ID.
        entry_data: Entry update data (all fields optional).
        session: Database session.
        current_user: The authenticated user.

    Returns:
        MilkEntry: The updated entry with supplier information.

    Raises:
        HTTPException: 404 if entry or new supplier not found.
    """
    # Get entry without loading relationship (we'll reload it fresh after update)
    statement = select(MilkEntry).where(MilkEntry.id == entry_id)
    result = await session.execute(statement)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    # If supplier_id is being updated, verify new supplier exists
    if entry_data.supplier_id is not None:
        supplier = await get_supplier_by_id(session, entry_data.supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found",
            )

    # Update only provided fields
    update_data = entry_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    session.add(entry)
    await session.commit()

    # Expire all cached objects to ensure fresh data on next query
    await session.run_sync(lambda sync_session: sync_session.expire_all())

    # Reload with fresh supplier relationship
    statement = (
        select(MilkEntry)
        .where(MilkEntry.id == entry_id)
        .options(selectinload(MilkEntry.supplier))
    )
    result = await session.execute(statement)
    return result.scalar_one()


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete milk entry",
    description="Permanently delete a milk entry.",
)
async def delete_entry(
    entry_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> None:
    """Delete a milk entry.

    Args:
        entry_id: The entry's ID.
        session: Database session.
        current_user: The authenticated user.

    Raises:
        HTTPException: 404 if entry not found.
    """
    statement = select(MilkEntry).where(MilkEntry.id == entry_id)
    result = await session.execute(statement)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found",
        )

    await session.delete(entry)
    await session.commit()
