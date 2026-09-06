"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { MetricCard } from "@/components/dashboard/metric-card";
import { api } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import {
  FileText,
  Download,
  ShieldCheck,
  Building,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Scale,
  Receipt,
  FileSpreadsheet,
} from "lucide-react";

export default function TaxPage() {
  const [days, setDays] = useState(90);

  const { data, isLoading } = useQuery({
    queryKey: ["taxReconciliation", days],
    queryFn: () => api.getTaxReconciliation(days),
  });

  const monthlyList = data?.monthly_breakdown || [];

  return (
    <div className="flex-1 pb-16">
      <Header days={days} onDaysChange={setDays} />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-7xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Tax Reconciliation
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Input Tax Credit (ITC), 1% GST TCS, and 0.1% Income Tax TDS.
            </p>
          </div>

          <a
            href={api.getTaxExportUrl()}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-slate-800 transition-colors self-start sm:self-auto"
          >
            <Download className="h-4 w-4" />
            <span>Export CSV</span>
          </a>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Claimable Input Tax Credit (ITC)"
            value={formatINR(data?.claimable_itc_gst || 0)}
            subtext="18% GST paid on seller commissions & fees"
            icon={ShieldCheck}
            variant="success"
          />

          <MetricCard
            title="1% GST TCS Withheld"
            value={formatINR(data?.tcs_gst_withheld || 0)}
            subtext="Section 52 CGST/SGST in Cash Ledger"
            icon={Building}
            variant="default"
          />

          <MetricCard
            title="0.1% Income Tax TDS (194-O)"
            value={formatINR(data?.tds_income_tax_194o || 0)}
            subtext="Withheld on gross sales (Form 26AS credit)"
            icon={Receipt}
            variant="default"
          />

          <MetricCard
            title="Est. Net GST Cash Payable"
            value={formatINR(data?.estimated_net_gst_payable || 0)}
            subtext="Output GST minus claimable ITC & TCS"
            icon={Scale}
            variant="warning"
          />
        </div>

        {/* Monthly Breakdown Table */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Monthly Tax Breakdown</h2>
              <p className="text-[11px] text-slate-500">
                Summary for GSTR-3B and income tax books
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-100 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Period / Month</th>
                  <th className="py-3 px-3 text-right">Orders</th>
                  <th className="py-3 px-3 text-right">Gross Sales</th>
                  <th className="py-3 px-3 text-right">Output GST</th>
                  <th className="py-3 px-3 text-right">Marketplace Fees</th>
                  <th className="py-3 px-4 text-right text-emerald-700 bg-emerald-50/50">Claimable ITC (18%)</th>
                  <th className="py-3 px-3 text-right">TCS GST (1%)</th>
                  <th className="py-3 px-3 text-right">TDS 194-O (0.1%)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-400">
                      Calculating tax reconciliation figures...
                    </td>
                  </tr>
                ) : monthlyList.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-400">
                      No order transactions found for tax reconciliation in this time window.
                    </td>
                  </tr>
                ) : (
                  monthlyList.map((m) => (
                    <tr key={m.month} className="hover:bg-slate-50/80 transition-colors font-mono text-[11px]">
                      <td className="py-3 px-4 font-sans font-semibold text-slate-900">{m.month}</td>
                      <td className="py-3 px-3 text-right font-sans text-slate-600">{m.orders_count}</td>
                      <td className="py-3 px-3 text-right text-slate-900">{formatINR(m.gross_sales)}</td>
                      <td className="py-3 px-3 text-right text-slate-700">{formatINR(m.output_gst)}</td>
                      <td className="py-3 px-3 text-right text-slate-700">{formatINR(m.marketplace_fees)}</td>
                      <td className="py-3 px-4 text-right font-bold text-emerald-600 bg-emerald-50/30">
                        {formatINR(m.claimable_itc)}
                      </td>
                      <td className="py-3 px-3 text-right text-blue-700">{formatINR(m.tcs_gst)}</td>
                      <td className="py-3 px-3 text-right text-purple-700">{formatINR(m.tds_194o)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* GSTR-3B Direct Mapping Reference */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5 text-slate-700" />
            <h3 className="text-sm font-bold text-slate-900">GSTR-3B Official Return Filing Box Reference</h3>
          </div>
          <p className="text-xs text-slate-500">
            Share this table or the exported CSV with your CA to populate your monthly GST return:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-4 space-y-2">
              <span className="inline-block rounded bg-slate-200 px-2 py-0.5 text-[10px] font-bold text-slate-700">
                Table 3.1(a)
              </span>
              <p className="text-xs font-semibold text-slate-800">Outward Taxable Supplies</p>
              <p className="text-[11px] text-slate-600">
                Gross sales of goods fulfilled via Amazon/Flipkart. Output GST collected on items must be reported here.
              </p>
            </div>

            <div className="rounded-lg border border-emerald-200 bg-emerald-50/30 p-4 space-y-2">
              <span className="inline-block rounded bg-emerald-200 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                Table 4.A(5)
              </span>
              <p className="text-xs font-semibold text-emerald-900">All Other ITC (Services)</p>
              <p className="text-[11px] text-slate-600">
                Enter total Claimable ITC ({formatINR(data?.claimable_itc_gst || 0)}) from Amazon & Flipkart tax invoices (GSTIN on seller tax statement).
              </p>
            </div>

            <div className="rounded-lg border border-blue-200 bg-blue-50/30 p-4 space-y-2">
              <span className="inline-block rounded bg-blue-200 px-2 py-0.5 text-[10px] font-bold text-blue-800">
                Table 6.1
              </span>
              <p className="text-xs font-semibold text-blue-900">Payment of Tax via Cash Ledger</p>
              <p className="text-[11px] text-slate-600">
                Use accumulated TCS ({formatINR(data?.tcs_gst_withheld || 0)}) deposited by marketplaces to offset any remaining cash tax liability.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

