"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { MetricCard } from "@/components/dashboard/metric-card";
import { api } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import {
  Megaphone,
  TrendingDown,
  Percent,
  Copy,
  Check,
  ShieldAlert,
  Sparkles,
  MousePointer,
  AlertTriangle,
  Lightbulb,
} from "lucide-react";

export default function AdvertisingPage() {
  const [days, setDays] = useState(30);
  const [copied, setCopied] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["ppcAudit", days],
    queryFn: () => api.getPPCAudit(days),
  });

  const campaigns = data?.campaigns || [];
  const negativeKws = data?.negative_keyword_recommendations || [];

  const handleCopyNegatives = () => {
    if (negativeKws.length > 0) {
      const kwList = negativeKws.map((k) => `${k.keyword} (${k.match_type})`).join("\n");
      navigator.clipboard.writeText(kwList);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex-1 pb-16">
      <Header days={days} onDaysChange={setDays} />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-7xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Advertising
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Campaign efficiency, ACOS tracking, and negative keyword optimization.
            </p>
          </div>

          <button
            onClick={handleCopyNegatives}
            className="flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-slate-800 transition-colors self-start sm:self-auto"
          >
            {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
            <span>{copied ? "Copied Negatives!" : "Copy Negative Keywords"}</span>
          </button>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Ad Spend"
            value={formatINR(data?.total_ad_spend)}
            subtext={`${data?.total_clicks || 0} clicks across campaigns`}
            icon={Megaphone}
            variant="default"
          />

          <MetricCard
            title="Attributed Ad Sales"
            value={formatINR(data?.total_ad_sales)}
            subtext={`${data?.blended_roas || "0.0"}x Return on Ad Spend (ROAS)`}
            icon={Percent}
            variant="success"
          />

          <MetricCard
            title="Blended ACOS"
            value={`${data?.blended_acos_percentage || "0.0"}%`}
            subtext="Target breakeven ACOS: 28%"
            icon={TrendingDown}
            variant={
              (data?.blended_acos_percentage || 0) > 40
                ? "danger"
                : (data?.blended_acos_percentage || 0) > 28
                ? "warning"
                : "success"
            }
          />

          <MetricCard
            title="Bleed Spend Recoverable"
            value={formatINR(data?.bleed_spend_recoverable)}
            subtext="Wasted on high-ACOS & non-converting terms"
            icon={ShieldAlert}
            variant="danger"
          />
        </div>

        {/* Main Grid: Campaign Table (2 cols) and Negative Keywords Studio (1 col) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Campaigns Table */}
          <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden flex flex-col justify-between">
            <div>
              <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">Campaign Performance</h2>
                  <p className="text-[11px] text-slate-500">Itemized ACOS, spend velocity, and bid recommendations</p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-100 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Campaign Name</th>
                      <th className="py-3 px-3 text-right">Spend</th>
                      <th className="py-3 px-3 text-right">Sales</th>
                      <th className="py-3 px-3 text-right">ACOS</th>
                      <th className="py-3 px-3 text-right">ROAS</th>
                      <th className="py-3 px-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {isLoading ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-slate-400">Loading ad campaigns...</td>
                      </tr>
                    ) : campaigns.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-slate-400">No campaigns found.</td>
                      </tr>
                    ) : (
                      campaigns.map((c, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                          <td className="py-3.5 px-4">
                            <div className="font-semibold text-slate-900">{c.campaign_name}</div>
                            <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                              <span>{c.marketplace}</span>
                              <span>•</span>
                              <span>{c.clicks} clicks</span>
                              <span>•</span>
                              <span>CPC: ₹{c.cpc}</span>
                            </div>
                            <div className="text-[11px] text-slate-600 mt-1 italic">
                              💡 {c.recommendation}
                            </div>
                          </td>
                          <td className="py-3.5 px-3 text-right font-mono font-medium text-slate-800">
                            {formatINR(c.spend)}
                          </td>
                          <td className="py-3.5 px-3 text-right font-mono font-semibold text-slate-900">
                            {formatINR(c.sales)}
                          </td>
                          <td className="py-3.5 px-3 text-right font-mono font-bold">
                            <span
                              className={
                                c.acos_percentage >= 45
                                  ? "text-rose-600"
                                  : c.acos_percentage >= 28
                                  ? "text-amber-600"
                                  : "text-emerald-600"
                              }
                            >
                              {c.acos_percentage}%
                            </span>
                          </td>
                          <td className="py-3.5 px-3 text-right font-mono text-slate-700">
                            {c.roas}x
                          </td>
                          <td className="py-3.5 px-3 text-center">
                            <span
                              className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                                c.status === "Severe Bleed"
                                  ? "bg-rose-100 text-rose-800"
                                  : c.status === "Watch"
                                  ? "bg-amber-100 text-amber-800"
                                  : "bg-emerald-100 text-emerald-800"
                              }`}
                            >
                              {c.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Negative Keywords Radar (1 col) */}
          <div className="space-y-6">
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">Negative Keyword Radar</h2>
                  <p className="text-[11px] text-slate-500">High-spend search queries with zero conversion intent</p>
                </div>
                <button
                  onClick={handleCopyNegatives}
                  className="p-1 text-slate-400 hover:text-slate-800"
                  title="Copy Negatives"
                >
                  {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
                </button>
              </div>

              <div className="space-y-3 pt-1">
                {negativeKws.map((neg, idx) => (
                  <div key={idx} className="rounded-lg border border-slate-100 bg-slate-50/70 p-3 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 font-mono">"{neg.keyword}"</span>
                      <span className="rounded bg-rose-50 text-rose-700 px-1.5 py-0.2 text-[10px] font-semibold border border-rose-200">
                        {neg.match_type}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600">{neg.reason}</p>
                    <div className="text-[11px] font-semibold text-emerald-700 pt-0.5">
                      Estimated Savings: {neg.estimated_monthly_savings}/mo
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Bid Optimization Rules */}
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-3">
              <div className="flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">AI Bid Action Checklist</h3>
              </div>
              <div className="space-y-2 pt-1">
                {data?.actionable_bid_optimizations.map((item, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-700 bg-slate-50 p-2 rounded-lg border border-slate-100">
                    <Check className="h-3.5 w-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

