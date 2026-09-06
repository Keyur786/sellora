"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { MetricCard } from "@/components/dashboard/metric-card";
import { api } from "@/lib/api";
import { formatINR, formatPercent } from "@/lib/utils";
import {
  Tag,
  TrendingUp,
  AlertCircle,
  Sparkles,
  Calculator,
  CheckCircle2,
  X,
  Layers,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { PriceSimulationResponse } from "@/types";

export default function PricingPage() {
  const [isSimOpen, setIsSimOpen] = useState(false);

  // Simulator Form State
  const [simCost, setSimCost] = useState("350");
  const [simPkg, setSimPkg] = useState("25");
  const [simShip, setSimShip] = useState("75");
  const [simTargetPrice, setSimTargetPrice] = useState("999");
  const [simCategory, setSimCategory] = useState("Home & Kitchen");
  const [simResult, setSimResult] = useState<PriceSimulationResponse | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["pricingRecommendations"],
    queryFn: () => api.getPricingRecommendations(),
  });

  const simMutation = useMutation({
    mutationFn: api.simulatePrice,
    onSuccess: (res) => {
      setSimResult(res);
    },
  });

  const recommendations = data?.sku_recommendations || [];

  const handleSimulate = (e: React.FormEvent) => {
    e.preventDefault();
    simMutation.mutate({
      cost_price: parseFloat(simCost) || 0,
      packaging_cost: parseFloat(simPkg) || 0,
      shipping_cost: parseFloat(simShip) || 0,
      target_selling_price: parseFloat(simTargetPrice) || 0,
      category: simCategory,
      marketplace: "amazon",
    });
  };

  const openSimWithSku = (cogs: string, current: string, cat: string) => {
    setSimCost(cogs);
    setSimTargetPrice(current);
    setSimCategory(cat);
    setSimResult(null);
    setIsSimOpen(true);
  };

  return (
    <div className="flex-1 pb-16">
      <Header />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-7xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Dynamic Pricing
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Breakeven floors, fee breakpoints, and price simulations.
            </p>
          </div>

          <button
            onClick={() => {
              setSimResult(null);
              setIsSimOpen(true);
            }}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-emerald-500 transition-colors self-start sm:self-auto"
          >
            <Calculator className="h-4 w-4" />
            <span>Price Simulator</span>
          </button>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Catalog SKUs Audited"
            value={`${data?.total_skus_evaluated || 0} Products`}
            subtext="Calculated breakeven floors"
            icon={Tag}
            variant="default"
          />

          <MetricCard
            title="Fee Breakpoint Sweet Spots"
            value={`${data?.breakpoint_opportunities_count || 0} SKUs`}
            subtext="Reprice under slabs to save fees"
            icon={TrendingUp}
            variant="warning"
          />

          <MetricCard
            title="Margin-At-Risk SKUs"
            value={`${data?.loss_making_skus_count || 0} SKUs`}
            subtext="Net profit margins under 10%"
            icon={AlertCircle}
            variant={data?.loss_making_skus_count ? "danger" : "success"}
          />

          <MetricCard
            title="Potential Annual Profit Uplift"
            value={formatINR(data?.estimated_annual_profit_uplift)}
            subtext="Via fee breakpoint optimization"
            icon={Sparkles}
            variant="success"
          />
        </div>

        {/* Pricing Recommendations Table */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Pricing & Margin Ledger</h2>
              <p className="text-[11px] text-slate-500">Breakeven thresholds and recommended optimal price points</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-100 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Product / SKU</th>
                  <th className="py-3 px-3 text-right">Current Price</th>
                  <th className="py-3 px-3 text-right">Breakeven Floor</th>
                  <th className="py-3 px-3 text-right">Recommended</th>
                  <th className="py-3 px-3 text-right">Net Margin</th>
                  <th className="py-3 px-4">Fee Opportunity & Profit Impact</th>
                  <th className="py-3 px-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-400">Auditing product pricing...</td>
                  </tr>
                ) : recommendations.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-400">No products found.</td>
                  </tr>
                ) : (
                  recommendations.map((item) => (
                    <tr key={item.sku} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900 max-w-xs truncate">{item.title}</div>
                        <div className="text-[11px] text-slate-400 font-mono">{item.sku} • {item.category}</div>
                      </td>
                      <td className="py-3.5 px-3 text-right font-mono font-medium text-slate-800">
                        {formatINR(item.current_price)}
                      </td>
                      <td className="py-3.5 px-3 text-right font-mono font-bold text-rose-600 bg-rose-50/30">
                        {formatINR(item.breakeven_floor_price)}
                      </td>
                      <td className="py-3.5 px-3 text-right font-mono font-bold text-emerald-600 bg-emerald-50/30">
                        {formatINR(item.recommended_optimal_price)}
                      </td>
                      <td className="py-3.5 px-3 text-right font-mono">
                        <span className="font-bold text-slate-900">{item.current_net_margin_percentage}%</span>
                        {item.projected_net_margin_percentage !== item.current_net_margin_percentage && (
                          <div className="text-[10px] text-emerald-600 font-semibold flex items-center justify-end gap-0.5">
                            <ArrowRight className="h-2.5 w-2.5" />
                            <span>{item.projected_net_margin_percentage}%</span>
                          </div>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        {item.fee_tier_opportunity && (
                          <div className="font-semibold text-slate-900 text-xs">{item.fee_tier_opportunity}</div>
                        )}
                        <div className="text-[11px] text-emerald-700 font-medium mt-0.5">
                          {item.expected_profit_impact}
                        </div>
                      </td>
                      <td className="py-3.5 px-3 text-center">
                        <button
                          onClick={() => openSimWithSku(item.cogs, item.current_price, item.category)}
                          className="rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
                        >
                          Simulate
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* What-If Price Simulation Modal */}
      {isSimOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-slate-200 bg-white shadow-xl overflow-hidden animate-in fade-in zoom-in duration-150 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
              <div className="flex items-center gap-2">
                <Calculator className="h-5 w-5 text-emerald-600" />
                <div>
                  <h3 className="text-base font-bold text-slate-900">What-If Selling Price Simulator</h3>
                  <p className="text-xs text-slate-500">Test any selling price against Amazon India fee slabs in real-time</p>
                </div>
              </div>
              <button
                onClick={() => setIsSimOpen(false)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4">
              <form onSubmit={handleSimulate} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700">Target Selling Price (₹) *</label>
                    <input
                      type="number"
                      step="1"
                      value={simTargetPrice}
                      onChange={(e) => setSimTargetPrice(e.target.value)}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500"
                      required
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700">Product Cost Price (₹) *</label>
                    <input
                      type="number"
                      step="1"
                      value={simCost}
                      onChange={(e) => setSimCost(e.target.value)}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:ring-2 focus:ring-emerald-500"
                      required
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700">Packaging Cost (₹)</label>
                    <input
                      type="number"
                      step="1"
                      value={simPkg}
                      onChange={(e) => setSimPkg(e.target.value)}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700">Shipping / EasyShip (₹)</label>
                    <input
                      type="number"
                      step="1"
                      value={simShip}
                      onChange={(e) => setSimShip(e.target.value)}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={simMutation.isPending}
                    className="flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2 text-xs font-semibold text-white hover:bg-emerald-500"
                  >
                    <Calculator className="h-4 w-4" />
                    <span>{simMutation.isPending ? "Calculating..." : "Simulate Economics"}</span>
                  </button>
                </div>
              </form>

              {/* Simulation Result */}
              {simResult && (
                <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 space-y-3 animate-in fade-in">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                    <span className="font-bold text-slate-900 text-xs">Simulated Unit Economics:</span>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                        simResult.is_profitable
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-rose-100 text-rose-800"
                      }`}
                    >
                      {simResult.is_profitable ? "Profitable" : "Loss-Making"}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="bg-white p-2.5 rounded border border-slate-100">
                      <span className="text-slate-500 block text-[10px] font-sans uppercase">Net Unit Profit</span>
                      <span className={`text-sm font-bold ${parseFloat(simResult.net_unit_profit) >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                        {formatINR(simResult.net_unit_profit)} ({simResult.net_margin_percentage}%)
                      </span>
                    </div>

                    <div className="bg-white p-2.5 rounded border border-slate-100">
                      <span className="text-slate-500 block text-[10px] font-sans uppercase">Breakeven Floor</span>
                      <span className="text-sm font-bold text-slate-900">
                        {formatINR(simResult.breakeven_price)}
                      </span>
                    </div>

                    <div className="bg-white p-2.5 rounded border border-slate-100">
                      <span className="text-slate-500 block text-[10px] font-sans uppercase">Referral Commission</span>
                      <span className="text-xs font-medium text-slate-700">
                        {formatINR(simResult.estimated_referral_fee)} ({simResult.referral_fee_rate_percentage}%)
                      </span>
                    </div>

                    <div className="bg-white p-2.5 rounded border border-slate-100">
                      <span className="text-slate-500 block text-[10px] font-sans uppercase">Closing Fee</span>
                      <span className="text-xs font-medium text-slate-700">
                        {formatINR(simResult.estimated_closing_fee)}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-700 bg-white p-2.5 rounded border border-slate-200">
                    💡 <strong>Verdict:</strong> {simResult.verdict}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

