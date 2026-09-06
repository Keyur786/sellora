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

  const { data: cfoData, isLoading: isLoadingCFO } = useQuery({
    queryKey: ["cfoInsights", days],
    queryFn: () => api.getCFOInsights(days),
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

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6">
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
            change={`${parseFloat(String(cfoData?.profit_variance_pct || 0)) >= 0 ? "+" : ""}${cfoData?.profit_variance_pct || "0.0"}% vs prev ${days}d`}
            isPositive={parseFloat(String(cfoData?.profit_variance_pct || 0)) >= 0}
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

        {/* Virtual CFO Executive Profit Diagnosis (AI) */}
        <div className="rounded-xl border border-emerald-200/80 bg-gradient-to-br from-emerald-50/70 via-white to-slate-50 p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-emerald-100/80 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-sm shadow-emerald-200">
                <span className="font-bold text-sm">₹AI</span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-slate-900">Profit Insights</h2>
                  <span className="rounded-full bg-emerald-100 border border-emerald-200 px-2 py-0.2 text-[10px] font-semibold text-emerald-800">
                    Live AI
                  </span>
                </div>
                <p className="text-[11px] text-slate-500">Comparing current {days}-day period to previous baseline</p>
              </div>
            </div>

            {cfoData && (
              <span
                className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${
                  parseFloat(cfoData.profit_variance) >= 0
                    ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                    : "bg-rose-100 text-rose-800 border border-rose-200"
                }`}
              >
                {parseFloat(cfoData.profit_variance) >= 0 ? "+" : ""}
                {formatINR(cfoData.profit_variance)} Net Variance ({cfoData.profit_variance_pct}%)
              </span>
            )}
          </div>

          {isLoadingCFO ? (
            <p className="text-xs text-slate-400 py-4 text-center">Synthesizing CFO diagnostics...</p>
          ) : !cfoData ? null : (
            <div className="space-y-4">
              <p className="text-xs font-semibold text-slate-900 bg-white/80 p-3 rounded-lg border border-emerald-100/60 shadow-2xs">
                {cfoData.headline}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Diagnoses */}
                <div className="space-y-2">
                  <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Root-Cause Findings</p>
                  <div className="space-y-1.5">
                    {cfoData.diagnoses.map((d, idx) => (
                      <div key={idx} className="text-xs text-slate-700 flex items-start gap-2 bg-white/60 p-2.5 rounded-lg border border-slate-100">
                        <span className="text-emerald-600 font-bold">•</span>
                        <span>{d}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Prioritized Actions */}
                <div className="space-y-2">
                  <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">High-ROI Next Actions</p>
                  <div className="space-y-1.5">
                    {cfoData.recommended_actions.map((act, idx) => (
                      <div key={idx} className="text-xs text-slate-800 font-medium flex items-start gap-2 bg-emerald-50/40 p-2.5 rounded-lg border border-emerald-100/80">
                        <span className="text-emerald-700 font-bold">✓</span>
                        <span>{act}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
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
