"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { ProfitTrendPoint } from "@/types";
import { formatINR } from "@/lib/utils";

interface ProfitChartProps {
  data: ProfitTrendPoint[];
}

export function ProfitChart({ data }: ProfitChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-80 items-center justify-center rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
        No trend data available for the selected period
      </div>
    );
  }

  // Format chart data numeric
  const formattedData = data.map((d) => ({
    date: d.date,
    Sales: typeof d.sales === "string" ? parseFloat(d.sales) : d.sales,
    "Net Profit": typeof d.net_profit === "string" ? parseFloat(d.net_profit) : d.net_profit,
    "Marketplace Fees": typeof d.marketplace_fees === "string" ? parseFloat(d.marketplace_fees) : d.marketplace_fees,
    Advertising: typeof d.advertising === "string" ? parseFloat(d.advertising) : d.advertising,
  }));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Revenue vs Real Net Profit</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Daily tracking after marketplace fees, shipping, taxes, and advertising spend
          </p>
        </div>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} />
            <YAxis
              stroke="#94a3b8"
              fontSize={12}
              tickLine={false}
              tickFormatter={(v) => `₹${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`}
            />
            <Tooltip
              formatter={(value: any) => [formatINR(value), ""]}
              contentStyle={{
                backgroundColor: "#ffffff",
                borderRadius: "8px",
                border: "1px solid #e2e8f0",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                fontSize: "12px",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }} />
            <Area
              type="monotone"
              dataKey="Sales"
              stroke="#3b82f6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorSales)"
            />
            <Area
              type="monotone"
              dataKey="Net Profit"
              stroke="#10b981"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorProfit)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
