from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_organization
from app.models.organization import Organization
from app.models.order import Order
from app.schemas.ai import (
    CFOInsightResponse,
    ListingGenerateRequest,
    ListingGenerateResponse,
    RTORiskResponse,
    OrdersRTOSummaryResponse,
    SentimentInsightResponse,
    DisputeClaimRequest,
    DisputeClaimResponse,
    PPCAnalyticsResponse,
    PricingAuditResponse,
    PriceSimulationRequest,
    PriceSimulationResponse,
    WorkingCapitalForecastResponse,
    AssistantChatRequest,
    AssistantChatResponse,
    WhatsAppDigestResponse,
)
from app.services.ai.cfo_service import CFOService
from app.services.ai.listing_service import ListingService
from app.services.ai.rto_risk_service import RTORiskService
from app.services.ai.sentiment_service import SentimentService
from app.services.ai.dispute_service import DisputeService
from app.services.ai.ppc_radar_service import PPCRadarService
from app.services.ai.pricing_engine import PricingEngine
from app.services.ai.forecasting_service import ForecastingService
from app.services.ai.assistant_service import AssistantService

router = APIRouter()


@router.get("/cfo-insights", response_model=CFOInsightResponse)
def get_cfo_insights(
    days: int = Query(default=30, ge=7, le=180),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Generate executive root-cause profit diagnostics comparing current period to previous period."""
    return CFOService.get_cfo_insights(db=db, org_id=org.id, days=days)


@router.post("/generate-listing", response_model=ListingGenerateResponse)
def generate_marketplace_listing(
    request: ListingGenerateRequest,
    org: Organization = Depends(get_current_organization),
):
    """Generate high-converting Amazon India & Flipkart titles, 5 bullets, and vernacular/Hinglish search terms."""
    return ListingService.generate_listing(request)


@router.get("/orders-risk-summary", response_model=OrdersRTOSummaryResponse)
def get_orders_rto_risk_summary(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Evaluate Cash-on-Delivery RTO doorstep rejection risk across recent orders."""
    return RTORiskService.get_orders_summary(db=db, org_id=org.id, limit=limit)


@router.get("/order-rto-risk/{order_id}", response_model=RTORiskResponse)
def get_single_order_rto_risk(
    order_id: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Evaluate COD RTO doorstep rejection risk for a specific order."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.organization_id == org.id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return RTORiskService.evaluate_order(order)


@router.get("/return-insights", response_model=SentimentInsightResponse)
def get_return_insights(
    days: int = Query(default=60, ge=7, le=180),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Analyze customer return reasons and identify packaging & factory defect root causes."""
    return SentimentService.get_return_insights(db=db, org_id=org.id, days=days)


@router.post("/draft-dispute", response_model=DisputeClaimResponse)
def draft_marketplace_dispute(
    request: DisputeClaimRequest,
    org: Organization = Depends(get_current_organization),
):
    """Generate ready-to-submit Amazon India SAFE-T or Flipkart SPF reimbursement claim letters."""
    return DisputeService.draft_dispute(request)


@router.get("/ppc-audit", response_model=PPCAnalyticsResponse)
def get_ppc_ad_audit(
    days: int = Query(default=30, ge=7, le=180),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Analyze PPC advertising spend, ACOS/ROAS bleed, and negative keyword opportunities."""
    return PPCRadarService.get_ppc_audit(db=db, org_id=org.id, days=days)


@router.get("/pricing-recommendations", response_model=PricingAuditResponse)
def get_pricing_recommendations(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Audit catalog pricing, calculate breakeven floors, and discover fee-tier breakpoint sweet spots."""
    return PricingEngine.audit_catalog_pricing(db=db, org_id=org.id)


@router.post("/simulate-price", response_model=PriceSimulationResponse)
def simulate_selling_price(
    request: PriceSimulationRequest,
    org: Organization = Depends(get_current_organization),
):
    """Simulate net profit, Amazon referral fees, and closing fee shifts for any custom selling price."""
    return PricingEngine.simulate_price(request)


@router.get("/forecasting", response_model=WorkingCapitalForecastResponse)
def get_inventory_forecast(
    season: str = Query(default="standard", description="Season mode: standard, festive, or diwali"),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Calculate Days of Inventory Remaining (DOIR), stockout alerts, and reorder working capital."""
    return ForecastingService.get_forecast(db=db, org_id=org.id, season=season)


@router.post("/chat", response_model=AssistantChatResponse)
def chat_with_assistant(
    request: AssistantChatRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Converse with Sellora's AI Seller Copilot in English or Hinglish with live store data grounding."""
    return AssistantService.chat(db=db, org_id=org.id, req=request)


@router.get("/whatsapp-digest", response_model=WhatsAppDigestResponse)
def get_whatsapp_morning_digest(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Generate daily morning 8:00 AM WhatsApp executive business briefing for store owner."""
    return AssistantService.get_whatsapp_digest(db=db, org_id=org.id)

