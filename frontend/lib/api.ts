import { DashboardResponse, Product, Order, MarketplaceAccount, ProfitTrendPoint, Organization } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API Error ${response.status}: ${errorBody || response.statusText}`);
  }

  return response.json();
}

export const api = {
  getOrganization: (): Promise<Organization> => {
    return request<Organization>("/organization/current");
  },

  updateOrganization: (data: { name?: string; currency?: string; timezone?: string }): Promise<Organization> => {
    return request<Organization>("/organization/current", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  getDashboard: (days = 30): Promise<DashboardResponse> => {
    return request<DashboardResponse>(`/dashboard?days=${days}`);
  },

  getProducts: (): Promise<Product[]> => {
    return request<Product[]>("/products");
  },

  createProduct: (data: {
    sku: string;
    title: string;
    asin_or_fsn?: string;
    category?: string;
    image_url?: string;
    cost_price: number;
    packaging_cost: number;
    other_cost: number;
    initial_stock?: number;
  }): Promise<Product> => {
    return request<Product>("/products", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  updateProductCOGS: (productId: string, data: { cost_price?: number; packaging_cost?: number; other_cost?: number }): Promise<Product> => {
    return request<Product>(`/products/${productId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  getOrders: (page = 1, pageSize = 20, marketplace?: string): Promise<{ orders: Order[]; total_count: number }> => {
    const mkt = marketplace ? `&marketplace_type=${marketplace}` : "";
    return request<{ orders: Order[]; total_count: number }>(`/orders?page=${page}&page_size=${pageSize}${mkt}`);
  },

  getOrder: (orderId: string): Promise<Order> => {
    return request<Order>(`/orders/${orderId}`);
  },

  getProfitTrends: (days = 14): Promise<ProfitTrendPoint[]> => {
    return request<ProfitTrendPoint[]>(`/profit/trends?days=${days}`);
  },

  getMarketplaces: (): Promise<MarketplaceAccount[]> => {
    return request<MarketplaceAccount[]>("/marketplaces");
  },

  updateMarketplaceCredentials: (
    accountId: string,
    data: import("@/types").MarketplaceCredentialsUpdate
  ): Promise<MarketplaceAccount> => {
    return request<MarketplaceAccount>(`/marketplaces/${accountId}/credentials`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  testAmazonConnection: (
    data: import("@/types").MarketplaceTestConnectionRequest
  ): Promise<import("@/types").MarketplaceTestConnectionResponse> => {
    return request<import("@/types").MarketplaceTestConnectionResponse>("/marketplaces/amazon/test-connection", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  syncMarketplace: (accountId: string): Promise<{ job_id: string; status: string; message: string }> => {
    return request<{ job_id: string; status: string; message: string }>(`/marketplaces/${accountId}/sync`, {
      method: "POST",
    });
  },

  uploadAmazonDateRangeReport: async (file: File): Promise<{
    success: boolean;
    message: string;
    rows_parsed: number;
    orders_imported: number;
    refunds_imported: number;
    fees_extracted: number;
    total_sales_value: string;
    skus_identified: number;
  }> => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${API_BASE_URL}/import/amazon/date-range-report`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const err = await response.text();
      throw new Error(err || "Failed to upload Amazon report");
    }
    return response.json();
  },

  uploadProductCOGS: async (file: File): Promise<{
    success: boolean;
    message: string;
    rows_processed: number;
    products_updated: number;
    products_created: number;
    updated_skus: string[];
  }> => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${API_BASE_URL}/import/products/cogs-csv`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const err = await response.text();
      throw new Error(err || "Failed to upload COGS CSV");
    }
    return response.json();
  },

  getSampleReportUrl: (reportType: string): string => {
    return `${API_BASE_URL}/import/sample/${reportType}`;
  },

  // Returns & RTO Analytics
  getReturnsAnalytics: (days = 30): Promise<import("@/types").ReturnsAnalyticsResponse> => {
    return request<import("@/types").ReturnsAnalyticsResponse>(`/returns/analytics?days=${days}`);
  },

  // Operational Expenses
  getExpenses: (days = 90, category?: string): Promise<import("@/types").Expense[]> => {
    const cat = category ? `&category=${category}` : "";
    return request<import("@/types").Expense[]>(`/expenses?days=${days}${cat}`);
  },

  createExpense: (data: {
    category: string;
    amount: number;
    currency?: string;
    date: string;
    description?: string;
    vendor_name?: string;
    payment_method?: string;
    is_recurring?: boolean;
  }): Promise<import("@/types").Expense> => {
    return request<import("@/types").Expense>("/expenses", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  deleteExpense: (id: string): Promise<void> => {
    return request<void>(`/expenses/${id}`, {
      method: "DELETE",
    });
  },

  getExpenseSummary: (days = 30): Promise<import("@/types").ExpenseSummaryResponse> => {
    return request<import("@/types").ExpenseSummaryResponse>(`/expenses/summary?days=${days}`);
  },

  // Tax Reconciliation
  getTaxReconciliation: (days = 90): Promise<import("@/types").TaxReconciliationResponse> => {
    return request<import("@/types").TaxReconciliationResponse>(`/tax/reconciliation?days=${days}`);
  },

  getTaxExportUrl: (): string => {
    return `${API_BASE_URL}/tax/export`;
  },

  // AI Suite & Copilot
  getCFOInsights: (days = 30): Promise<import("@/types").CFOInsightResponse> => {
    return request<import("@/types").CFOInsightResponse>(`/ai/cfo-insights?days=${days}`);
  },

  generateListing: (data: import("@/types").ListingGenerateRequest): Promise<import("@/types").ListingGenerateResponse> => {
    return request<import("@/types").ListingGenerateResponse>("/ai/generate-listing", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  getOrdersRTOSummary: (limit = 50): Promise<import("@/types").OrdersRTOSummaryResponse> => {
    return request<import("@/types").OrdersRTOSummaryResponse>(`/ai/orders-risk-summary?limit=${limit}`);
  },

  getOrderRTORisk: (orderId: string): Promise<import("@/types").RTORiskResponse> => {
    return request<import("@/types").RTORiskResponse>(`/ai/order-rto-risk/${orderId}`);
  },

  getReturnInsights: (days = 60): Promise<import("@/types").SentimentInsightResponse> => {
    return request<import("@/types").SentimentInsightResponse>(`/ai/return-insights?days=${days}`);
  },

  draftDispute: (data: import("@/types").DisputeClaimRequest): Promise<import("@/types").DisputeClaimResponse> => {
    return request<import("@/types").DisputeClaimResponse>("/ai/draft-dispute", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  getPPCAudit: (days = 30): Promise<import("@/types").PPCAnalyticsResponse> => {
    return request<import("@/types").PPCAnalyticsResponse>(`/ai/ppc-audit?days=${days}`);
  },

  getPricingRecommendations: (): Promise<import("@/types").PricingAuditResponse> => {
    return request<import("@/types").PricingAuditResponse>("/ai/pricing-recommendations");
  },

  simulatePrice: (data: import("@/types").PriceSimulationRequest): Promise<import("@/types").PriceSimulationResponse> => {
    return request<import("@/types").PriceSimulationResponse>("/ai/simulate-price", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  getForecasting: (season = "standard"): Promise<import("@/types").WorkingCapitalForecastResponse> => {
    return request<import("@/types").WorkingCapitalForecastResponse>(`/ai/forecasting?season=${season}`);
  },

  chatWithAssistant: (data: import("@/types").AssistantChatRequest): Promise<import("@/types").AssistantChatResponse> => {
    return request<import("@/types").AssistantChatResponse>("/ai/chat", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  getWhatsAppDigest: (): Promise<import("@/types").WhatsAppDigestResponse> => {
    return request<import("@/types").WhatsAppDigestResponse>("/ai/whatsapp-digest");
  },
};


