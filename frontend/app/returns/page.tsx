"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { formatINR, formatPercent } from "@/lib/utils";
import {
  RotateCcw,
  Truck,
  PackageX,
  AlertTriangle,
  TrendingDown,
  Info,
  ShieldAlert,
  Sparkles,
  FileText,
  Copy,
  Check,
  X,
  ShieldCheck,
  Scale,
} from "lucide-react";
import { MetricCard } from "@/components/dashboard/metric-card";
import { DisputeClaimResponse } from "@/types";

export default function ReturnsPage() {
  const [days, setDays] = useState(30);

  // Dispute Claim Modal State
  const [isDisputeOpen, setIsDisputeOpen] = useState(false);
  const [orderId, setOrderId] = useState("");
  const [claimType, setClaimType] = useState("wrong_item_received");
  const [marketplace, setMarketplace] = useState("amazon");
  const [lossAmount, setLossAmount] = useState("999");
  const [claimNotes, setClaimNotes] = useState("");
  const [disputeResult, setDisputeResult] = useState<DisputeClaimResponse | null>(null);
  const [copiedLetter, setCopiedLetter] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["returnsAnalytics", days],
    queryFn: () => api.getReturnsAnalytics(days),
  });

  const { data: aiInsights, isLoading: isLoadingAi } = useQuery({
    queryKey: ["returnInsights", days],
    queryFn: () => api.getReturnInsights(days),
  });

  const disputeMutation = useMutation({
    mutationFn: api.draftDispute,
    onSuccess: (res) => {
      setDisputeResult(res);
    },
  });

  const skuRanking = data?.sku_ranking || [];
  const reasons = data?.reasons_breakdown || [];

  const handleDraftSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    disputeMutation.mutate({
      order_id: orderId,
      claim_type: claimType,
      marketplace,
      loss_amount: parseFloat(lossAmount) || 0,
      notes: claimNotes,
    });
  };

  const copyClaimLetter = () => {
    if (disputeResult) {
      navigator.clipboard.writeText(`${disputeResult.subject_line}\n\n${disputeResult.formal_claim_letter}`);
      setCopiedLetter(true);
      setTimeout(() => setCopiedLetter(false), 2000);
    }
  };

  return (
    <div className="flex-1 pb-16">
      <Header days={days} onDaysChange={setDays} />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-7xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Returns & RTO</h1>
            <p className="text-xs text-slate-500 mt-1">
              Doorstep rejections, return analytics, and dispute claims.
            </p>
          </div>

          <button
            onClick={() => {
              setDisputeResult(null);
              setIsDisputeOpen(true);
            }}
            className="flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-slate-800 transition-colors self-start sm:self-auto"
          >
            <Sparkles className="h-4 w-4 text-emerald-400" />
            <span>Draft SAFE-T Dispute</span>
          </button>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Returns & RTO"
            value={`${data?.total_returns || 0} Units`}
            subtext={`${data?.overall_return_rate_percentage || "0.00"}% of total orders`}
            icon={RotateCcw}
            variant="warning"
          />

          <MetricCard
            title="Courier RTO"
            value={`${data?.courier_rto_count || 0} Units`}
            subtext={`${data?.courier_rto_rate_percentage || "0.00"}% COD rejection rate`}
            icon={Truck}
            variant="danger"
          />

          <MetricCard
            title="Total Financial Loss"
            value={formatINR(data?.total_financial_loss)}
            subtext="Lost freight, packaging & write-offs"
            icon={TrendingDown}
            variant="danger"
          />

          <MetricCard
            title="Courier Freight Bleed"
            value={formatINR(data?.shipping_loss)}
            subtext="Forward & reverse shipping wasted"
            icon={PackageX}
            variant="default"
          />
        </div>

        {/* AI Root-Cause Diagnostic & Supplier Feedback Banner */}
        <div className="rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50/50 via-white to-slate-50 p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-emerald-100 pb-3">
            <Sparkles className="h-4 w-4 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-900">Return Diagnostics & Packaging Feedback</h2>
            <span className="rounded-full bg-emerald-100 px-2 py-0.2 text-[10px] font-semibold text-emerald-800">
              Sentiment Analysis
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Top Root Cause Issues */}
            <div className="space-y-3">
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Categorized Return Vulnerabilities</p>
              {isLoadingAi ? (
                <p className="text-xs text-slate-400">Mining return reasons...</p>
              ) : !aiInsights?.top_issues || aiInsights.top_issues.length === 0 ? (
                <p className="text-xs text-slate-400">No return issues detected.</p>
              ) : (
                aiInsights.top_issues.map((issue, idx) => (
                  <div key={idx} className="rounded-lg border border-slate-100 bg-white p-3 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900">{issue.root_cause}</span>
                      <span className="font-semibold text-rose-600">{issue.percentage}%</span>
                    </div>
                    <p className="text-[11px] text-slate-600">{issue.summary}</p>
                    <div className="pt-1 text-[11px] text-emerald-700 font-medium">
                      <strong>Fix:</strong> {issue.remedy}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Factory & Warehouse Protocol Checklist */}
            <div className="space-y-3">
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Actionable Supplier & Packing Protocol</p>
              <div className="space-y-2">
                {aiInsights?.actionable_supplier_feedback.map((fb, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-700 bg-white p-2.5 rounded-lg border border-slate-100">
                    <Check className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    <span>{fb}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Grid: SKU Ranking and Reason Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* SKU Risk Table (2 Columns wide) */}
          <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden flex flex-col justify-between">
            <div>
              <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">SKU-Level Return & RTO Ranking</h2>
                  <p className="text-[11px] text-slate-500">Products causing the largest courier and inventory write-off losses</p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-100 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Product / SKU</th>
                      <th className="py-3 px-3 text-right">Sold</th>
                      <th className="py-3 px-3 text-right">Returns</th>
                      <th className="py-3 px-3 text-right">RTOs</th>
                      <th className="py-3 px-3 text-right">Return %</th>
                      <th className="py-3 px-4 text-right">Net Loss</th>
                      <th className="py-3 px-3 text-center">Risk</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {isLoading ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-slate-400">Loading returns analysis...</td>
                      </tr>
                    ) : skuRanking.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-slate-400">No return records found for this period.</td>
                      </tr>
                    ) : (
                      skuRanking.map((item) => (
                        <tr key={item.sku} className="hover:bg-slate-50/80 transition-colors">
                          <td className="py-3 px-4">
                            <div className="font-semibold text-slate-900 max-w-xs truncate">{item.title}</div>
                            <div className="font-mono text-[11px] text-slate-400">{item.sku}</div>
                          </td>
                          <td className="py-3 px-3 text-right font-medium">{item.units_sold}</td>
                          <td className="py-3 px-3 text-right">{item.returns_count}</td>
                          <td className="py-3 px-3 text-right font-semibold text-amber-700">{item.rto_count}</td>
                          <td className="py-3 px-3 text-right font-bold text-slate-900">{item.return_rate_percentage}%</td>
                          <td className="py-3 px-4 text-right font-bold text-rose-600 font-mono">
                            {formatINR(item.total_loss)}
                          </td>
                          <td className="py-3 px-3 text-center">
                            <span
                              className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                                item.risk_level === "High"
                                  ? "bg-rose-100 text-rose-800"
                                  : item.risk_level === "Medium"
                                  ? "bg-amber-100 text-amber-800"
                                  : "bg-emerald-100 text-emerald-800"
                              }`}
                            >
                              {item.risk_level} Risk
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

          {/* Return Reasons Breakdown (1 Column wide) */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-900">Return & RTO Root Causes</h2>
            <p className="text-[11px] text-slate-500">Distribution of customer and courier rejection reasons</p>

            <div className="space-y-3 pt-2">
              {reasons.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-6">No return reasons logged.</p>
              ) : (
                reasons.map((r, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs font-medium">
                      <span className="text-slate-700 truncate max-w-[200px]">{r.reason}</span>
                      <span className="font-semibold text-slate-900">{r.percentage}% ({r.count})</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-rose-500 transition-all"
                        style={{ width: `${Math.min(100, r.percentage)}%` }}
                      ></div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="mt-6 rounded-lg bg-slate-50 p-3 text-[11px] text-slate-600 space-y-1.5 border border-slate-100">
              <p className="font-semibold text-slate-800">Actionable Advice:</p>
              <p>• Disable COD on SKUs with &gt; 25% RTO rate</p>
              <p>• Add size charts to listings for apparel items</p>
              <p>• Upgrade packaging on glass/copper fragile goods</p>
            </div>
          </div>
        </div>
      </main>

      {/* 1-Click SAFE-T Dispute Modal */}
      {isDisputeOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl rounded-xl border border-slate-200 bg-white shadow-xl overflow-hidden animate-in fade-in zoom-in duration-150 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-600" />
                <div>
                  <h3 className="text-base font-bold text-slate-900">Marketplace Dispute & SAFE-T Drafter</h3>
                  <p className="text-xs text-slate-500">Draft official reimbursement claims for fraud returns or transit damage</p>
                </div>
              </div>
              <button
                onClick={() => setIsDisputeOpen(false)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4">
              {!disputeResult ? (
                <form onSubmit={handleDraftSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700">Marketplace *</label>
                      <select
                        value={marketplace}
                        onChange={(e) => setMarketplace(e.target.value)}
                        className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      >
                        <option value="amazon">Amazon India (SAFE-T Claim)</option>
                        <option value="flipkart">Flipkart (Seller Protection Fund - SPF)</option>
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700">Claim Type *</label>
                      <select
                        value={claimType}
                        onChange={(e) => setClaimType(e.target.value)}
                        className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      >
                        <option value="wrong_item_received">Customer Fraud / Wrong Item Returned</option>
                        <option value="courier_transit_damage">Damaged in Transit by Courier</option>
                        <option value="weight_discrepancy">Excess Weight Handling Overcharge</option>
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700">Order ID *</label>
                      <input
                        type="text"
                        placeholder="e.g. 408-1234567-8901234"
                        value={orderId}
                        onChange={(e) => setOrderId(e.target.value)}
                        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        required
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-slate-700">Claimed Loss Amount (₹) *</label>
                      <input
                        type="number"
                        step="0.01"
                        placeholder="999.00"
                        value={lossAmount}
                        onChange={(e) => setLossAmount(e.target.value)}
                        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        required
                      />
                    </div>

                    <div className="sm:col-span-2 space-y-1">
                      <label className="text-xs font-semibold text-slate-700">Inspection Observations / Notes</label>
                      <textarea
                        rows={2}
                        placeholder="e.g. Received a used bar of soap instead of the copper water bottle. Outer courier bag was torn and retaped."
                        value={claimNotes}
                        onChange={(e) => setClaimNotes(e.target.value)}
                        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => setIsDisputeOpen(false)}
                      className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={disputeMutation.isPending}
                      className="flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2 text-xs font-semibold text-white hover:bg-emerald-500"
                    >
                      <Sparkles className="h-4 w-4" />
                      <span>{disputeMutation.isPending ? "Drafting..." : "Generate Dispute Claim"}</span>
                    </button>
                  </div>
                </form>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-emerald-100 text-emerald-800 px-2 py-0.5 text-[10px] font-bold uppercase">
                      {disputeResult.marketplace.toUpperCase()} Official Claim Draft
                    </span>
                    <button
                      onClick={copyClaimLetter}
                      className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 transition-colors"
                    >
                      {copiedLetter ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                      <span>{copiedLetter ? "Copied to Clipboard!" : "Copy Claim Letter"}</span>
                    </button>
                  </div>

                  {/* Subject Line */}
                  <div className="space-y-1">
                    <label className="text-[11px] font-bold text-slate-500 uppercase">Subject Line</label>
                    <p className="text-xs font-semibold text-slate-900 bg-slate-50 p-2.5 rounded border border-slate-200 font-mono">
                      {disputeResult.subject_line}
                    </p>
                  </div>

                  {/* Formal Claim Letter */}
                  <div className="space-y-1">
                    <label className="text-[11px] font-bold text-slate-500 uppercase">Formal Claim Body</label>
                    <pre className="text-xs text-slate-800 bg-slate-50 p-3.5 rounded-lg border border-slate-200 font-mono whitespace-pre-wrap leading-relaxed">
                      {disputeResult.formal_claim_letter}
                    </pre>
                  </div>

                  {/* Evidence Checklist */}
                  <div className="space-y-2 rounded-lg bg-amber-50 p-3.5 border border-amber-200 text-xs">
                    <p className="font-bold text-amber-950">Required Evidence to Attach Before Submitting:</p>
                    <div className="space-y-1 text-amber-900">
                      {disputeResult.required_evidence_checklist.map((ev, idx) => (
                        <div key={idx} className="flex items-start gap-2">
                          <Check className="h-3.5 w-3.5 text-amber-700 shrink-0 mt-0.5" />
                          <span>{ev}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <button
                      onClick={() => setDisputeResult(null)}
                      className="text-xs text-slate-500 hover:text-slate-800"
                    >
                      ← Draft another claim
                    </button>
                    <button
                      onClick={() => setIsDisputeOpen(false)}
                      className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                    >
                      Close
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
