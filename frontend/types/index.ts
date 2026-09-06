export interface Organization {
  id: string;
  name: string;
  currency: string;
  slug?: string;
  timezone?: string;
  is_active?: boolean;
  created_at?: string;
}

export interface ProfitSummary {
  currency: string;
  total_sales: number | string;
  total_orders: number;
  units_sold: number;
  net_profit: number | string;
  profit_margin_percentage: number | string;
  product_costs: number | string;
  packaging_costs: number | string;
  marketplace_fees: number | string;
  shipping_costs: number | string;
  advertising_costs: number | string;
  returns_costs: number | string;
  other_expenses: number | string;
}

export interface ProductProfitItem {
  product_id: string;
  sku: string;
  title: string;
  image_url?: string;
  units_sold: number;
  gross_sales: number | string;
  product_cost: number | string;
  packaging_cost: number | string;
  marketplace_fees: number | string;
  shipping_cost: number | string;
  advertising_cost: number | string;
  returns_cost: number | string;
  net_profit: number | string;
  profit_margin_percentage: number | string;
}

export interface Product {
  id: string;
  sku: string;
  title: string;
  asin_or_fsn?: string;
  category?: string;
  image_url?: string;
  cost_price: number | string;
  packaging_cost: number | string;
  other_cost: number | string;
  is_active: boolean;
  available_stock: number;
}

export interface OrderItem {
  id: string;
  sku: string;
  title: string;
  quantity: number;
  item_price: number | string;
  shipping_price: number | string;
  item_tax: number | string;
  shipping_tax: number | string;
  discount_amount: number | string;
}

export interface Fee {
  id: string;
  fee_type: string;
  amount: number | string;
  currency: string;
  description?: string;
}

export interface Order {
  id: string;
  marketplace_type: "amazon" | "flipkart" | string;
  marketplace_order_id: string;
  order_date: string;
  status: string;
  fulfillment_channel?: string;
  total_amount: number | string;
  currency: string;
  customer_city?: string;
  customer_state?: string;
  items: OrderItem[];
  fees: Fee[];
}

export interface MarketplaceAccount {
  id: string;
  marketplace_type: "amazon" | "flipkart" | string;
  account_name: string;
  seller_id: string;
  marketplace_id?: string;
  status: "connected" | "error" | "syncing" | "disconnected";
  is_active: boolean;
  has_credentials?: boolean;
  connection_mode?: "live" | "sandbox";
  last_synced_at?: string;
}

export interface MarketplaceCredentialsUpdate {
  seller_id?: string;
  marketplace_id?: string;
  client_id?: string;
  client_secret?: string;
  refresh_token?: string;
}

export interface MarketplaceTestConnectionRequest {
  marketplace_type?: string;
  seller_id?: string;
  client_id?: string;
  client_secret?: string;
  refresh_token?: string;
  marketplace_id?: string;
}

export interface MarketplaceTestConnectionResponse {
  success: boolean;
  connection_mode: "live" | "sandbox";
  message: string;
  marketplace_name: string;
  seller_id?: string;
  checked_at: string;
}

export interface ProfitTrendPoint {
  date: string;
  sales: number | string;
  net_profit: number | string;
  marketplace_fees: number | string;
  advertising: number | string;
}

export interface DashboardResponse {
  organization: Organization;
  summary: ProfitSummary;
  top_products: ProductProfitItem[];
  recent_orders: Order[];
}

export interface ReturnReasonItem {
  reason: string;
  count: number;
  percentage: number;
}

export interface SkuReturnItem {
  sku: string;
  title: string;
  units_sold: number;
  returns_count: number;
  rto_count: number;
  customer_return_count: number;
  return_rate_percentage: number;
  total_loss: string;
  risk_level: "Low" | "Medium" | "High";
}

export interface ReturnsAnalyticsResponse {
  period_days: number;
  total_units_sold: number;
  total_returns: number;
  overall_return_rate_percentage: string;
  courier_rto_count: number;
  courier_rto_rate_percentage: string;
  customer_return_count: number;
  total_financial_loss: string;
  shipping_loss: string;
  packaging_loss: string;
  damaged_product_loss: string;
  reasons_breakdown: ReturnReasonItem[];
  sku_ranking: SkuReturnItem[];
}

export interface Expense {
  id: string;
  organization_id: string;
  category: string;
  amount: number | string;
  currency: string;
  date: string;
  description?: string;
  vendor_name?: string;
  payment_method?: string;
  is_recurring: boolean;
  created_at: string;
}

export interface ExpenseCategorySummary {
  category: string;
  total_amount: number | string;
  percentage: number;
  count: number;
}

export interface ExpenseSummaryResponse {
  currency: string;
  total_expenses: number | string;
  period_days: number;
  categories: ExpenseCategorySummary[];
}

export interface MonthlyTaxItem {
  month: string;
  orders_count: number;
  gross_sales: string;
  output_gst: string;
  marketplace_fees: string;
  claimable_itc: string;
  tcs_gst: string;
  tds_194o: string;
}

export interface TaxReconciliationResponse {
  currency: string;
  period_days: number;
  gross_marketplace_sales: string;
  output_gst_collected: string;
  total_marketplace_fees: string;
  claimable_itc_gst: string;
  tcs_gst_withheld: string;
  tds_income_tax_194o: string;
  estimated_net_gst_payable: string;
  monthly_breakdown: MonthlyTaxItem[];
}

export interface CFOInsightResponse {
  period_days: number;
  currency: string;
  current_profit: string;
  previous_profit: string;
  profit_variance: string;
  profit_variance_pct: string;
  headline: string;
  diagnoses: string[];
  critical_alerts: string[];
  recommended_actions: string[];
}

export interface ListingGenerateRequest {
  sku?: string;
  title: string;
  category: string;
  marketplace: string;
  material_or_specs?: string;
  key_features?: string;
  target_audience?: string;
  selling_price?: number;
}

export interface ListingGenerateResponse {
  marketplace: string;
  optimized_title: string;
  bullet_points: string[];
  backend_search_terms: string[];
  vernacular_keywords: string[];
  product_description: string;
  policy_compliance_notes: string[];
}

export interface RTORiskResponse {
  order_id: string;
  marketplace_order_id: string;
  payment_method: string;
  total_amount: string;
  customer_city?: string;
  customer_state?: string;
  risk_score: number;
  risk_level: "Low" | "Medium" | "High";
  risk_reasons: string[];
  recommended_mitigation: string;
}

export interface OrdersRTOSummaryResponse {
  total_orders_evaluated: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  potential_rto_loss_at_risk: string;
  orders: RTORiskResponse[];
}

export interface ReturnSentimentItem {
  root_cause: string;
  percentage: number;
  affected_skus: string[];
  summary: string;
  remedy: string;
}

export interface SentimentInsightResponse {
  period_days: number;
  total_analyzed_returns: number;
  top_issues: ReturnSentimentItem[];
  actionable_supplier_feedback: string[];
}

export interface DisputeClaimRequest {
  order_id: string;
  claim_type: string;
  marketplace: string;
  loss_amount: number;
  notes?: string;
}

export interface DisputeClaimResponse {
  claim_type: string;
  marketplace: string;
  subject_line: string;
  formal_claim_letter: string;
  required_evidence_checklist: string[];
  policy_citation: string;
}

export interface CampaignAuditItem {
  campaign_name: string;
  marketplace: string;
  spend: string;
  sales: string;
  acos_percentage: number;
  roas: number;
  clicks: number;
  impressions: number;
  cpc: string;
  status: "Profitable" | "Watch" | "Severe Bleed" | string;
  recommendation: string;
}

export interface NegativeKeywordRecommendation {
  keyword: string;
  match_type: string;
  reason: string;
  estimated_monthly_savings: string;
}

export interface PPCAnalyticsResponse {
  currency: string;
  period_days: number;
  total_ad_spend: string;
  total_ad_sales: string;
  blended_acos_percentage: number;
  blended_roas: number;
  total_clicks: number;
  total_impressions: number;
  bleed_spend_recoverable: string;
  campaigns: CampaignAuditItem[];
  negative_keyword_recommendations: NegativeKeywordRecommendation[];
  actionable_bid_optimizations: string[];
}

export interface PricingRecommendationItem {
  sku: string;
  title: string;
  category: string;
  current_price: string;
  cogs: string;
  packaging_cost: string;
  shipping_cost: string;
  breakeven_floor_price: string;
  recommended_optimal_price: string;
  current_net_margin_percentage: number;
  projected_net_margin_percentage: number;
  fee_tier_opportunity?: string;
  expected_profit_impact: string;
  action_verdict: "Reduce to Hit Fee Breakpoint" | "Healthy" | "Increase to Protect Margin" | string;
}

export interface PricingAuditResponse {
  currency: string;
  total_skus_evaluated: number;
  loss_making_skus_count: number;
  breakpoint_opportunities_count: number;
  estimated_annual_profit_uplift: string;
  sku_recommendations: PricingRecommendationItem[];
}

export interface PriceSimulationRequest {
  sku?: string;
  cost_price: number;
  packaging_cost?: number;
  shipping_cost?: number;
  target_selling_price: number;
  marketplace?: string;
  category?: string;
}

export interface PriceSimulationResponse {
  target_selling_price: string;
  cost_price: string;
  packaging_cost: string;
  shipping_cost: string;
  estimated_referral_fee: string;
  referral_fee_rate_percentage: number;
  estimated_closing_fee: string;
  gst_tcs_tds: string;
  total_marketplace_fees: string;
  net_unit_profit: string;
  net_margin_percentage: number;
  breakeven_price: string;
  is_profitable: boolean;
  verdict: string;
}

export interface ForecastingSKUItem {
  sku: string;
  title: string;
  category: string;
  current_stock: number;
  reserved_stock: number;
  daily_velocity_units: number;
  days_of_inventory_remaining: number;
  seasonal_multiplier_applied: number;
  status: "Critical Stockout Risk" | "Reorder Soon" | "Healthy" | "Dead Stock / LTSF" | string;
  recommended_reorder_units: number;
  reorder_deadline_date: string;
  working_capital_required: string;
  action_notes: string;
}

export interface WorkingCapitalForecastResponse {
  currency: string;
  season_mode: string;
  total_skus_tracked: number;
  imminent_stockout_count: number;
  dead_stock_count: number;
  total_working_capital_required: string;
  average_catalog_doir_days: number;
  forecast_horizon_days: number;
  sku_forecasts: ForecastingSKUItem[];
}

export interface AssistantChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AssistantChatRequest {
  message: string;
  conversation_history?: AssistantChatMessage[];
}

export interface AssistantChatResponse {
  reply: string;
  suggested_followups: string[];
  context_tags: string[];
}

export interface WhatsAppDigestResponse {
  recipient_name: string;
  store_name: string;
  report_date: string;
  message_text: string;
  whatsapp_direct_url: string;
}


