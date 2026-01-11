"""Reports router for generating milk collection reports."""

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy import extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth import CurrentUser
from app.database import get_session
from app.models import MilkEntry, Supplier
from app.schemas import MonthlyReport, SupplierReport

router = APIRouter(tags=["reports"])

# Type alias for database session dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/monthly/{year}/{month}",
    response_model=MonthlyReport,
    summary="Get monthly payment report",
    description="Get a monthly report aggregating milk entries by supplier with payment calculations.",
)
async def get_monthly_report(
    year: int = Path(..., description="Report year"),
    month: int = Path(..., ge=1, le=12, description="Report month (1-12)"),
    session: SessionDep = None,
    current_user: CurrentUser = None,
) -> MonthlyReport:
    """Get monthly payment report.

    Aggregates all milk entries for the specified year/month, grouped by supplier.
    Calculates total liters and total amount (liters * rate_per_liter) per supplier.
    Only includes entries from active suppliers.

    Args:
        year: The report year.
        month: The report month (1-12).
        session: Database session.
        current_user: The authenticated user.

    Returns:
        MonthlyReport: Report with supplier aggregations and grand totals.
    """
    # Query to aggregate entries by supplier for the given month/year
    # Only include active suppliers
    statement = (
        select(
            Supplier.id.label("supplier_id"),
            Supplier.name.label("supplier_name"),
            Supplier.milk_type.label("milk_type"),
            Supplier.rate_per_liter.label("rate_per_liter"),
            func.coalesce(func.sum(MilkEntry.liters), 0.0).label("total_liters"),
        )
        .join(MilkEntry, MilkEntry.supplier_id == Supplier.id)
        .where(
            Supplier.is_active == True,  # noqa: E712
            extract("year", MilkEntry.date) == year,
            extract("month", MilkEntry.date) == month,
        )
        .group_by(
            Supplier.id,
            Supplier.name,
            Supplier.milk_type,
            Supplier.rate_per_liter,
        )
    )

    result = await session.execute(statement)
    rows = result.all()

    # Build supplier reports
    supplier_reports: list[SupplierReport] = []
    grand_total_liters = 0.0
    grand_total_amount = 0.0

    for row in rows:
        total_liters = float(row.total_liters)
        rate_per_liter = float(row.rate_per_liter)
        total_amount = total_liters * rate_per_liter

        supplier_report = SupplierReport(
            supplier_id=row.supplier_id,
            supplier_name=row.supplier_name,
            milk_type=row.milk_type,
            rate_per_liter=rate_per_liter,
            total_liters=total_liters,
            total_amount=total_amount,
        )
        supplier_reports.append(supplier_report)

        grand_total_liters += total_liters
        grand_total_amount += total_amount

    return MonthlyReport(
        year=year,
        month=month,
        suppliers=supplier_reports,
        grand_total_liters=grand_total_liters,
        grand_total_amount=grand_total_amount,
    )
