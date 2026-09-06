from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import get_current_organization
from app.models.organization import Organization
from app.models.financials import Expense
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseSummaryResponse, ExpenseCategorySummary

router = APIRouter()


@router.get("", response_model=List[ExpenseResponse])
def get_expenses(
    category: Optional[str] = Query(default=None),
    days: int = Query(default=90, ge=1, le=365),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve operational business expenses for the tenant."""
    since_date = date.today() - timedelta(days=days)
    query = (
        db.query(Expense)
        .filter(Expense.organization_id == org.id, Expense.date >= since_date)
        .order_by(Expense.date.desc())
    )
    if category:
        query = query.filter(Expense.category.ilike(f"%{category}%"))

    expenses = query.limit(limit).all()
    return [ExpenseResponse.model_validate(e) for e in expenses]


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Log a new business overhead expense (Rent, Salaries, Software, Packaging, CA)."""
    expense = Expense(
        organization_id=org.id,
        category=data.category,
        amount=data.amount,
        currency=data.currency,
        date=data.date,
        description=data.description,
        vendor_name=data.vendor_name,
        payment_method=data.payment_method,
        is_recurring=data.is_recurring,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return ExpenseResponse.model_validate(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Delete an operational expense record."""
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.organization_id == org.id)
        .first()
    )
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )

    db.delete(expense)
    db.commit()
    return None


@router.get("/summary", response_model=ExpenseSummaryResponse)
def get_expense_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve category-wise expense breakdown and total OPEX."""
    since_date = date.today() - timedelta(days=days)
    expenses = (
        db.query(Expense)
        .filter(Expense.organization_id == org.id, Expense.date >= since_date)
        .all()
    )

    total = sum((e.amount for e in expenses), Decimal("0.00"))
    cat_totals: dict[str, Decimal] = {}
    cat_counts: dict[str, int] = {}

    for e in expenses:
        cat_totals[e.category] = cat_totals.get(e.category, Decimal("0.00")) + e.amount
        cat_counts[e.category] = cat_counts.get(e.category, 0) + 1

    categories = []
    for cat, amt in cat_totals.items():
        pct = float((amt / total * Decimal("100"))) if total > Decimal("0.00") else 0.0
        categories.append(
            ExpenseCategorySummary(
                category=cat,
                total_amount=amt,
                percentage=round(pct, 1),
                count=cat_counts[cat],
            )
        )

    categories.sort(key=lambda x: x.total_amount, reverse=True)

    return ExpenseSummaryResponse(
        currency="INR",
        total_expenses=total,
        period_days=days,
        categories=categories,
    )

