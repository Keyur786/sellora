"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  IndianRupee,
  ShoppingCart,
  TrendingUp,
  Percent,
  Receipt,
  Megaphone,
  RotateCcw,
  Boxes,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { MetricCard } from "@/components/dashboard/metric-card";
import { ProfitChart } from "@/components/dashboard/profit-chart";
import { ProductProfitTable } from "@/components/dashboard/product-profit-table";
import { RecentOrders } from "@/components/dashboard/recent-orders";
import { api } from "@/lib/api";
import { formatINR, formatPercent } from "@/lib/utils";

export default function DashboardPage() {
  const [days, setDays] = useState(30);
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["dashboard", days],
    queryFn: () => api.getDashboard(days),
  });

  const { data: trendData } = useQuery({
    queryKey: ["profitTrends", days],
    queryFn: () => api.getProfitTrends(days),
  });

  const syncMutation = useMutation({
    mutationFn: () => api.syncMarketplace("demo"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["profitTrends"] });
    },
  });

  const summary = data?.summary;
  const topProducts = data?.top_products || [];
  const recentOrders = data?.recent_orders || [];

  return (
    <div className="flex-1 pb-12">
      <Header
        days={days}
        onDaysChange={setDays}
        onRefresh={() => syncMutation.mutate()}
        isRefreshing={syncMutation.isPending}
      />

      <main className="px-8 py-6 space-y-6">
        {/* Top KPI Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Sales"
            value={formatINR(summary?.total_sales)}
            subtext={`${summary?.total_orders || 0} orders placed`}
            icon={IndianRupee}
            variant="default"
          />

          <MetricCard
            title="Real Net Profit"
            value={formatINR(summary?.net_profit)}
            subtext="After all fees, COGS & ads"
            change="+18.4% vs last period"
            isPositive={true}
            icon={TrendingUp}
            variant="success"
          />

          <MetricCard
            title="Profit Margin"
            value={formatPercent(summary?.profit_margin_percentage)}
            subtext="Net margin on revenue"
            icon={Percent}
            variant={
              parseFloat(String(summary?.profit_margin_percentage || 0)) > 20
                ? "success"
                : "warning"
            }
          />

          <MetricCard
            title="Marketplace Fees"
            value={formatINR(summary?.marketplace_fees)}
            subtext="Commission, closing & pick-pack"
            icon={Receipt}
            variant="warning"
          />
        </div>

        {/* Secondary KPI Row */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <MetricCard
            title="Advertising Spend"
            value={formatINR(summary?.advertising_costs)}
            subtext="Amazon Sponsored Ads & Flipkart PLA"
            icon={Megaphone}
            variant="default"
          />
          <MetricCard
            title="Product Costs (COGS)"
            value={formatINR(
              parseFloat(String(summary?.product_costs || 0)) +
                parseFloat(String(summary?.packaging_costs || 0))
            )}
            subtext="Acquisition & packaging materials"
            icon={Boxes}
            variant="default"
          />
          <MetricCard
            title="Returns & RTO"
            value={formatINR(summary?.returns_costs)}
            subtext="Courier RTO & customer returns"
            icon={RotateCcw}
            variant="danger"
          />
        </div>

        {/* Chart */}
        <ProfitChart data={trendData || []} />

        {/* Product Profitability Breakdown Table */}
        <ProductProfitTable products={topProducts} isLoading={isLoading} />

        {/* Recent Orders */}
        <RecentOrders orders={recentOrders} />
      </main>
    </div>
  );
}
