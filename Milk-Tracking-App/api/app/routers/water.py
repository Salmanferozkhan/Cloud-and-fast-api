"""Water router for managing water bottle delivery entries."""

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth import CurrentUser
from app.database import get_session
from app.models import WaterEntry
from app.schemas import (
    WaterEntryCreate,
    WaterEntryResponse,
    WaterEntryUpdate,
    WaterMonthlyReport,
)

router = APIRouter(tags=["water"])

# Type alias for database session dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Default rate applied when client omits rate_per_bottle on create
DEFAULT_RATE_PER_BOTTLE = 80.0


@router.post(
    "",
    response_model=WaterEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new water bottle entry",
    description="Create a new water bottle delivery entry with date, bottles, and optional rate.",
)
async def create_water_entry(
    entry_data: WaterEntryCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> WaterEntry:
    """Create a new water bottle entry.

    Args:
        entry_data: Entry creation data (date, bottles, optional rate_per_bottle).
        session: Database session.
        current_user: The authenticated user.

    Returns:
        WaterEntry: The created entry.
    """
    rate = (
        entry_data.rate_per_bottle
        if entry_data.rate_per_bottle is not None
        else DEFAULT_RATE_PER_BOTTLE
    )

    entry = WaterEntry(
        date=entry_data.date,
        bottles=entry_data.bottles,
        rate_per_bottle=rate,
    )

    session.add(entry)
    await session.commit()
    await session.refresh(entry)

    return entry


@router.get(
    "",
    response_model=list[WaterEntryResponse],
    summary="List all water bottle entries",
    description="Get a list of all water bottle entries with optional date filters.",
)
async def list_water_entries(
    session: SessionDep,
    current_user: CurrentUser,
    start_date: dt.date | None = Query(default=None, description="Filter entries from this date"),
    end_date: dt.date | None = Query(default=None, description="Filter entries until this date"),
) -> list[WaterEntry]:
    """List all water bottle entries with optional date filters.

    Args:
        session: Database session.
        current_user: The authenticated user.
        start_date: Optional start date filter (inclusive).
        end_date: Optional end date filter (inclusive).

    Returns:
        list[WaterEntry]: List of water bottle entries ordered by date desc.
    """
    statement = select(WaterEntry)

    if start_date:
        statement = statement.where(WaterEntry.date >= start_date)
    if end_date:
        statement = statement.where(WaterEntry.date <= end_date)

    statement = statement.order_by(WaterEntry.date.desc())

    result = await session.execute(statement)
    entries = result.scalars().all()

    return list(entries)


@router.get(
    "/reports/monthly/{year}/{month}",
    response_model=WaterMonthlyReport,
    summary="Get monthly water bottle report",
    description="Get a monthly aggregation of water bottle entries with payment totals.",
)
async def get_monthly_water_report(
    session: SessionDep,
    current_user: CurrentUser,
    year: int = Path(..., description="Report year"),
    month: int = Path(..., ge=1, le=12, description="Report month (1-12)"),
) -> WaterMonthlyReport:
    """Get monthly water bottle payment report.

    Aggregates water entries for the specified year/month. Computes total bottles,
    total amount (sum of bottles * rate_per_bottle per row), the weighted average
    rate (total_amount / total_bottles), and the number of entries.

    Args:
        session: Database session.
        current_user: The authenticated user.
        year: The report year.
        month: The report month (1-12).

    Returns:
        WaterMonthlyReport: Monthly aggregation with totals and weighted average rate.
    """
    statement = select(
        func.coalesce(func.sum(WaterEntry.bottles), 0).label("total_bottles"),
        func.coalesce(
            func.sum(WaterEntry.bottles * WaterEntry.rate_per_bottle), 0.0
        ).label("total_amount"),
        func.count(WaterEntry.id).label("entry_count"),
    ).where(
        extract("year", WaterEntry.date) == year,
        extract("month", WaterEntry.date) == month,
    )

    result = await session.execute(statement)
    row = result.one()

    total_bottles = int(row.total_bottles)
    total_amount = float(row.total_amount)
    entry_count = int(row.entry_count)
    rate_avg = total_amount / total_bottles if total_bottles > 0 else 0.0

    return WaterMonthlyReport(
        year=year,
        month=month,
        total_bottles=total_bottles,
        rate_per_bottle_avg=rate_avg,
        total_amount=total_amount,
        entry_count=entry_count,
    )


@router.get(
    "/{entry_id}",
    response_model=WaterEntryResponse,
    summary="Get water entry by ID",
    description="Get a specific water bottle entry by its ID.",
)
async def get_water_entry_by_id(
    entry_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> WaterEntry:
    """Get a water bottle entry by ID.

    Args:
        entry_id: The entry's ID.
        session: Database session.
        current_user: The authenticated user.

    Returns:
        WaterEntry: The requested entry.

    Raises:
        HTTPException: 404 if entry not found.
    """
    statement = select(WaterEntry).where(WaterEntry.id == entry_id)
    result = await session.execute(statement)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Water entry not found",
        )

    return entry


@router.patch(
    "/{entry_id}",
    response_model=WaterEntryResponse,
    summary="Update water entry",
    description="Update a water bottle entry's information. All fields are optional.",
)
async def update_water_entry(
    entry_id: int,
    entry_data: WaterEntryUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> WaterEntry:
    """Update a water bottle entry.

    Args:
        entry_id: The entry's ID.
        entry_data: Entry update data (all fields optional).
        session: Database session.
        current_user: The authenticated user.

    Returns:
        WaterEntry: The updated entry.

    Raises:
        HTTPException: 404 if entry not found.
    """
    statement = select(WaterEntry).where(WaterEntry.id == entry_id)
    result = await session.execute(statement)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Water entry not found",
        )

    update_data = entry_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    session.add(entry)
    await session.commit()
    await session.refresh(entry)

    return entry


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete water entry",
    description="Permanently delete a water bottle entry.",
)
async def delete_water_entry(
    entry_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> None:
    """Delete a water bottle entry.

    Args:
        entry_id: The entry's ID.
        session: Database session.
        current_user: The authenticated user.

    Raises:
        HTTPException: 404 if entry not found.
    """
    statement = select(WaterEntry).where(WaterEntry.id == entry_id)
    result = await session.execute(statement)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Water entry not found",
        )

    await session.delete(entry)
    await session.commit()
