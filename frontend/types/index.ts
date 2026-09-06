export interface Organization {
  id: string;
  name: string;
  currency: string;
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
  last_synced_at?: string;
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
