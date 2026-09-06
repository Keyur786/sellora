from typing import List, Optional
from pydantic import BaseModel, Field


# --- Virtual CFO Profit Diagnostics ---
class CFOInsightResponse(BaseModel):
    period_days: int
    currency: str = "INR"
    current_profit: str
    previous_profit: str
    profit_variance: str
    profit_variance_pct: str
    headline: str
    diagnoses: List[str]
    critical_alerts: List[str]
    recommended_actions: List[str]


# --- AI Marketplace Listing Generator ---
class ListingGenerateRequest(BaseModel):
    sku: Optional[str] = None
    title: str
    category: str
    marketplace: str = "amazon"  # "amazon" or "flipkart"
    material_or_specs: Optional[str] = None
    key_features: Optional[str] = None
    target_audience: Optional[str] = None
    selling_price: Optional[float] = None


class ListingGenerateResponse(BaseModel):
    marketplace: str
    optimized_title: str
    bullet_points: List[str]
    backend_search_terms: List[str]
    vernacular_keywords: List[str]
    product_description: str
    policy_compliance_notes: List[str]


# --- Predictive COD RTO Risk Scorer ---
class RTORiskResponse(BaseModel):
    order_id: str
    marketplace_order_id: str
    payment_method: str
    total_amount: str
    customer_city: Optional[str] = None
    customer_state: Optional[str] = None
    risk_score: int  # 0 to 100
    risk_level: str  # "Low", "Medium", "High"
    risk_reasons: List[str]
    recommended_mitigation: str


class OrdersRTOSummaryResponse(BaseModel):
    total_orders_evaluated: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    potential_rto_loss_at_risk: str
    orders: List[RTORiskResponse]


# --- Return & Review Sentiment Miner ---
class ReturnSentimentItem(BaseModel):
    root_cause: str
    percentage: float
    affected_skus: List[str]
    summary: str
    remedy: str


class SentimentInsightResponse(BaseModel):
    period_days: int
    total_analyzed_returns: int
    top_issues: List[ReturnSentimentItem]
    actionable_supplier_feedback: List[str]


# --- Marketplace Dispute & SAFE-T Drafter ---
class DisputeClaimRequest(BaseModel):
    order_id: str
    claim_type: str  # "wrong_item_received", "courier_transit_damage", "weight_discrepancy", "unreturned_inventory"
    marketplace: str = "amazon"  # "amazon" or "flipkart"
    loss_amount: float
    notes: Optional[str] = None


class DisputeClaimResponse(BaseModel):
    claim_type: str
    marketplace: str
    subject_line: str
    formal_claim_letter: str
    required_evidence_checklist: List[str]
    policy_citation: str


# --- PPC Sponsored Ads Waste Radar ---
class CampaignAuditItem(BaseModel):
    campaign_name: str
    marketplace: str
    spend: str
    sales: str
    acos_percentage: float
    roas: float
    clicks: int
    impressions: int
    cpc: str
    status: str  # "Profitable", "Watch", "Severe Bleed"
    recommendation: str


class NegativeKeywordRecommendation(BaseModel):
    keyword: str
    match_type: str  # "Negative Exact", "Negative Phrase"
    reason: str
    estimated_monthly_savings: str


class PPCAnalyticsResponse(BaseModel):
    currency: str = "INR"
    period_days: int
    total_ad_spend: str
    total_ad_sales: str
    blended_acos_percentage: float
    blended_roas: float
    total_clicks: int
    total_impressions: int
    bleed_spend_recoverable: str
    campaigns: List[CampaignAuditItem]
    negative_keyword_recommendations: List[NegativeKeywordRecommendation]
    actionable_bid_optimizations: List[str]


# --- Margin-Guarded Dynamic Pricing & Buy Box Engine ---
class PricingRecommendationItem(BaseModel):
    sku: str
    title: str
    category: str
    current_price: str
    cogs: str
    packaging_cost: str
    shipping_cost: str
    breakeven_floor_price: str
    recommended_optimal_price: str
    current_net_margin_percentage: float
    projected_net_margin_percentage: float
    fee_tier_opportunity: Optional[str] = None
    expected_profit_impact: str
    action_verdict: str  # "Reduce to Hit Fee Breakpoint", "Healthy", "Increase to Protect Margin"


class PricingAuditResponse(BaseModel):
    currency: str = "INR"
    total_skus_evaluated: int
    loss_making_skus_count: int
    breakpoint_opportunities_count: int
    estimated_annual_profit_uplift: str
    sku_recommendations: List[PricingRecommendationItem]


class PriceSimulationRequest(BaseModel):
    sku: Optional[str] = None
    cost_price: float
    packaging_cost: float = 25.0
    shipping_cost: float = 75.0
    target_selling_price: float
    marketplace: str = "amazon"
    category: str = "General"


class PriceSimulationResponse(BaseModel):
    target_selling_price: str
    cost_price: str
    packaging_cost: str
    shipping_cost: str
    estimated_referral_fee: str
    referral_fee_rate_percentage: float
    estimated_closing_fee: str
    gst_tcs_tds: str
    total_marketplace_fees: str
    net_unit_profit: str
    net_margin_percentage: float
    breakeven_price: str
    is_profitable: bool
    verdict: str


# --- Demand & Working Capital Forecasting ---
class ForecastingSKUItem(BaseModel):
    sku: str
    title: str
    category: str
    current_stock: int
    reserved_stock: int
    daily_velocity_units: float
    days_of_inventory_remaining: float
    seasonal_multiplier_applied: float
    status: str  # "Critical Stockout Risk", "Reorder Soon", "Healthy", "Dead Stock / LTSF"
    recommended_reorder_units: int
    reorder_deadline_date: str
    working_capital_required: str
    action_notes: str


class WorkingCapitalForecastResponse(BaseModel):
    currency: str = "INR"
    season_mode: str  # "Standard", "Diwali & Great Indian Festival (3x)", "Festive Season (2x)"
    total_skus_tracked: int
    imminent_stockout_count: int
    dead_stock_count: int
    total_working_capital_required: str
    average_catalog_doir_days: float
    forecast_horizon_days: int = 30
    sku_forecasts: List[ForecastingSKUItem]


# --- Omnichannel Conversational Copilot & WhatsApp Digest ---
class AssistantChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class AssistantChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[AssistantChatMessage]] = None


class AssistantChatResponse(BaseModel):
    reply: str
    suggested_followups: List[str]
    context_tags: List[str]


class WhatsAppDigestResponse(BaseModel):
    recipient_name: str
    store_name: str
    report_date: str
    message_text: str
    whatsapp_direct_url: str


