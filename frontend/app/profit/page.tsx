"use client";

import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { formatINR, formatPercent } from "@/lib/utils";
import { CheckCircle2, TrendingUp, AlertTriangle } from "lucide-react";

export default function ProfitBreakdownPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", 30],
    queryFn: () => api.getDashboard(30),
  });

  const summary = data?.summary;

  const sales = parseFloat(String(summary?.total_sales || 0));
  const cogs = parseFloat(String(summary?.product_costs || 0));
  const packaging = parseFloat(String(summary?.packaging_costs || 0));
  const fees = parseFloat(String(summary?.marketplace_fees || 0));
  const shipping = parseFloat(String(summary?.shipping_costs || 0));
  const ads = parseFloat(String(summary?.advertising_costs || 0));
  const returns = parseFloat(String(summary?.returns_costs || 0));
  const other = parseFloat(String(summary?.other_expenses || 0));
  const netProfit = parseFloat(String(summary?.net_profit || 0));
  const margin = parseFloat(String(summary?.profit_margin_percentage || 0));

  const items = [
    { label: "Gross Marketplace Sales (Revenue)", value: sales, isPositive: true, isRevenue: true },
    { label: "Product Acquisition Cost (COGS)", value: -cogs, note: "Supplier & raw materials" },
    { label: "Packaging Supplies", value: -packaging, note: "Boxes, tape, bubble wrap" },
    { label: "Marketplace Commission & Closing Fees", value: -fees, note: "Amazon & Flipkart referral fee" },
    { label: "Shipping & Fulfillment (EasyShip / FBA)", value: -shipping, note: "Logistics and delivery fees" },
    { label: "Advertising & Sponsored Product Ads", value: -ads, note: "PPC ad campaigns" },
    { label: "Customer Returns & RTO Losses", value: -returns, note: "Courier return restocking" },
    { label: "Operating & Overhead Expenses", value: -other, note: "Office, software, tools" },
  ];

  return (
    <div className="flex-1 pb-12">
      <Header />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Profit Waterfall</h1>
          <p className="text-xs text-slate-500 mt-1">
            Revenue to net profit reconciliation across all deductions.
          </p>
        </div>

        {/* Net Profit Banner */}
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-6 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider">
              Real Net Profit
            </span>
            <div className="mt-1 text-3xl font-extrabold text-emerald-900">{formatINR(netProfit)}</div>
          </div>
          <div className="rounded-lg bg-white p-4 border border-emerald-200 text-center sm:text-right">
            <span className="text-xs text-slate-500 font-medium">Net Profit Margin</span>
            <div className="text-2xl font-bold text-emerald-700">{formatPercent(margin)}</div>
            <span className="text-[11px] text-slate-400">Target: &gt; 20%</span>
          </div>
        </div>

        {/* Waterfall Table */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-100 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3.5 px-6">Accounting Line Item</th>
                  <th className="py-3.5 px-4">Description / Breakdown</th>
                  <th className="py-3.5 px-6 text-right">Amount (INR ₹)</th>
                  <th className="py-3.5 px-4 text-right">% of Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {items.map((item, idx) => {
                  const pct = sales > 0 ? (Math.abs(item.value) / sales) * 100 : 0;
                  return (
                    <tr
                      key={idx}
                      className={item.isRevenue ? "bg-slate-50 font-semibold" : "hover:bg-slate-50/60 transition-colors"}
                    >
                      <td className="py-3.5 px-6 font-medium text-slate-900">{item.label}</td>
                      <td className="py-3.5 px-4 text-slate-500">{item.note || "-"}</td>
                      <td className={`py-3.5 px-6 text-right font-mono font-semibold ${item.isPositive ? "text-slate-900" : "text-rose-600"}`}>
                        {item.isPositive ? formatINR(item.value) : `-${formatINR(Math.abs(item.value))}`}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono text-slate-500">
                        {item.isRevenue ? "100.00%" : `-${pct.toFixed(2)}%`}
                      </td>
                    </tr>
                  );
                })}
                {/* Total row */}
                <tr className="bg-emerald-50/80 font-bold border-t-2 border-emerald-200 text-emerald-950">
                  <td className="py-4 px-6 text-sm">REAL NET PROFIT</td>
                  <td className="py-4 px-4 text-xs font-normal text-emerald-800">Final retained business profit</td>
                  <td className="py-4 px-6 text-right font-mono text-base text-emerald-800">{formatINR(netProfit)}</td>
                  <td className="py-4 px-4 text-right font-mono text-sm text-emerald-800">{formatPercent(margin)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
