from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_organization
from app.models.organization import Organization
from app.services.tax_engine import TaxEngine
from app.schemas.tax import TaxReconciliationResponse

router = APIRouter()


@router.get("/reconciliation", response_model=TaxReconciliationResponse)
def get_tax_reconciliation(
    days: int = Query(default=90, ge=30, le=365),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve Indian marketplace tax reconciliation (GSTR-3B ITC, Section 52 TCS, Section 194-O TDS)."""
    data = TaxEngine.get_tax_reconciliation(db=db, org_id=org.id, days=days)
    return TaxReconciliationResponse(**data)


@router.get("/export")
def export_ca_tax_report(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Download clean CSV tax reconciliation report formatted for Chartered Accountants (CA)."""
    csv_content = TaxEngine.generate_ca_csv(db=db, org_id=org.id)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sellora_ca_tax_reconciliation.csv"},
    )

