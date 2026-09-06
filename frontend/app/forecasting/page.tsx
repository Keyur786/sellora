"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { MetricCard } from "@/components/dashboard/metric-card";
import { api } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import {
  CalendarClock,
  AlertTriangle,
  Boxes,
  IndianRupee,
  Clock,
  Sparkles,
  Flame,
  ShieldCheck,
} from "lucide-react";

export default function ForecastingPage() {
  const [season, setSeason] = useState<string>("diwali");

  const { data, isLoading } = useQuery({
    queryKey: ["forecasting", season],
    queryFn: () => api.getForecasting(season),
  });

  const forecasts = data?.sku_forecasts || [];

  return (
    <div className="flex-1 pb-16">
      <Header />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-7xl">
        {/* Page Header & Seasonal Multiplier Selector */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Demand Forecasting
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Inventory runway, seasonal sales multipliers, and working capital planning.
            </p>
          </div>

          {/* Season Mode Toggle */}
          <div className="flex items-center rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
            <button
              onClick={() => setSeason("standard")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                season === "standard"
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Standard (1.0x)
            </button>
            <button
              onClick={() => setSeason("festive")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                season === "festive"
                  ? "bg-amber-500 text-white"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Festive (2.0x)
            </button>
            <button
              onClick={() => setSeason("diwali")}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                season === "diwali"
                  ? "bg-rose-600 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Flame className="h-3.5 w-3.5" />
              <span>Diwali Surge (3.0x)</span>
            </button>
          </div>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Working Capital Required"
            value={formatINR(data?.total_working_capital_required)}
            subtext="For 30-day stock buffer"
            icon={IndianRupee}
            variant="warning"
          />

          <MetricCard
            title="Critical Stockout Risk"
            value={`${data?.imminent_stockout_count || 0} SKUs`}
            subtext="Under 14 days inventory left"
            icon={AlertTriangle}
            variant={data?.imminent_stockout_count ? "danger" : "success"}
          />

          <MetricCard
            title="Dead Stock / LTSF"
            value={`${data?.dead_stock_count || 0} SKUs`}
            subtext="Over 90 days sitting inventory"
            icon={Boxes}
            variant="default"
          />

          <MetricCard
            title="Avg Catalog Runway"
            value={`${data?.average_catalog_doir_days || 0} Days`}
            subtext={data?.season_mode || "Standard"}
            icon={Clock}
            variant="default"
          />
        </div>

        {/* SKU Forecast Ledger Table */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900">SKU Inventory & Reorder Recommendations</h2>
              <p className="text-[11px] text-slate-500">
                Modeled for: <strong>{data?.season_mode}</strong> • 14-day lead time buffer
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-100 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Product / SKU</th>
                  <th className="py-3 px-3 text-right">Available Stock</th>
                  <th className="py-3 px-3 text-right">Velocity (Units/Day)</th>
                  <th className="py-3 px-3 text-right">Runway (DOIR)</th>
                  <th className="py-3 px-3 text-center">Stock Status</th>
                  <th className="py-3 px-3 text-right">Reorder Quantity</th>
                  <th className="py-3 px-3 text-right">PO Deadline</th>
                  <th className="py-3 px-4 text-right">Capital Needed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-400">Calculating inventory forecast...</td>
                  </tr>
                ) : forecasts.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-400">No inventory records found.</td>
                  </tr>
                ) : (
                  forecasts.map((item) => (
                    <tr key={item.sku} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900 max-w-xs truncate">{item.title}</div>
                        <div className="text-[11px] text-slate-400 font-mono">{item.sku} • {item.category}</div>
                      </td>
                      <td className="py-3.5 px-3 text-right font-medium text-slate-900">
                        {item.current_stock} <span className="text-[10px] text-slate-400">({item.reserved_stock} res)</span>
                      </td>
                      <td className="py-3.5 px-3 text-right font-mono font-medium text-slate-800">
                        {item.daily_velocity_units} /day
                      </td>
                      <td className="py-3.5 px-3 text-right font-mono font-bold">
                        <span
                          className={
                            item.days_of_inventory_remaining <= 14
                              ? "text-rose-600"
                              : item.days_of_inventory_remaining <= 28
                              ? "text-amber-600"
                              : "text-slate-900"
                          }
                        >
                          {item.days_of_inventory_remaining} days
                        </span>
                      </td>
                      <td className="py-3.5 px-3 text-center">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                            item.status === "Critical Stockout Risk"
                              ? "bg-rose-100 text-rose-800 border border-rose-200"
                              : item.status === "Reorder Soon"
                              ? "bg-amber-100 text-amber-800 border border-amber-200"
                              : item.status === "Dead Stock / LTSF"
                              ? "bg-purple-100 text-purple-800 border border-purple-200"
                              : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-3 text-right font-mono font-bold text-slate-900">
                        {item.recommended_reorder_units > 0 ? (
                          <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                            +{item.recommended_reorder_units} units
                          </span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-3 text-right font-mono text-[11px] text-slate-600">
                        {item.reorder_deadline_date}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-slate-900">
                        {item.recommended_reorder_units > 0 ? formatINR(item.working_capital_required) : "₹0.00"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

