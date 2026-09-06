"use client";

import { useState, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import Link from "next/link";
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  Download,
  ArrowRight,
  ShieldCheck,
  HelpCircle,
  Clock,
  Sparkles,
} from "lucide-react";

export default function ImportPage() {
  const queryClient = useQueryClient();

  // Amazon Report State
  const [amazonFile, setAmazonFile] = useState<File | null>(null);
  const [amazonResult, setAmazonResult] = useState<any>(null);
  const [amazonError, setAmazonError] = useState<string | null>(null);
  const amazonInputRef = useRef<HTMLInputElement>(null);

  // COGS State
  const [cogsFile, setCogsFile] = useState<File | null>(null);
  const [cogsResult, setCogsResult] = useState<any>(null);
  const [cogsError, setCogsError] = useState<string | null>(null);
  const cogsInputRef = useRef<HTMLInputElement>(null);

  // Amazon Upload Mutation
  const amazonMutation = useMutation({
    mutationFn: (file: File) => api.uploadAmazonDateRangeReport(file),
    onSuccess: (data) => {
      setAmazonResult(data);
      setAmazonError(null);
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: (err: any) => {
      setAmazonError(err.message || "Failed to process report");
    },
  });

  // COGS Upload Mutation
  const cogsMutation = useMutation({
    mutationFn: (file: File) => api.uploadProductCOGS(file),
    onSuccess: (data) => {
      setCogsResult(data);
      setCogsError(null);
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (err: any) => {
      setCogsError(err.message || "Failed to process COGS CSV");
    },
  });

  return (
    <div className="flex-1 pb-16">
      <Header />

      <main className="px-8 py-6 space-y-8 max-w-5xl">
        {/* Page Title & Context */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Data Import Center</h1>
            <p className="text-xs text-slate-500 mt-1">
              Upload your actual Amazon India transaction reports and supplier cost sheets to immediately see your real profit.
            </p>
          </div>

          {(amazonResult || cogsResult) && (
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-emerald-700 transition-colors"
            >
              <span>View Updated Profit Dashboard</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          )}
        </div>

        {/* Info Banner */}
        <div className="rounded-xl border border-blue-200 bg-blue-50/60 p-4 flex items-start gap-3 text-xs text-blue-900">
          <Sparkles className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold">No waiting for Amazon SP-API developer vetting</p>
            <p className="text-blue-700 leading-relaxed">
              Amazon Seller Central generates standard Date Range Transaction Reports containing every single real rupee
              deduction (commissions, closing fees, shipping, TCS, TDS). Uploading these reports provides 100% accurate,
              auditable profit analytics instantly.
            </p>
          </div>
        </div>

        {/* Two Import Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card 1: Amazon India Date Range Report */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500 font-bold text-white shadow-sm">
                    a
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-900">Amazon India Transaction Report</h2>
                    <p className="text-[11px] text-slate-400">Payments Date Range Report (.csv)</p>
                  </div>
                </div>
                <a
                  href={api.getSampleReportUrl("amazon_date_range")}
                  download="amazon_india_date_range_sample.csv"
                  className="flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-[11px] font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                  title="Download sample template"
                >
                  <Download className="h-3 w-3" />
                  <span>Sample</span>
                </a>
              </div>

              {/* Where to get it instructions */}
              <div className="rounded-lg bg-slate-50 p-3 text-[11px] text-slate-600 space-y-1">
                <p className="font-semibold text-slate-700">Where to get this from Seller Central:</p>
                <p>1. Go to <strong>Payments → Reports Repository</strong></p>
                <p>2. Select <strong>Date Range Reports</strong></p>
                <p>3. Click <strong>Generate Report → Transaction</strong> (.csv)</p>
              </div>

              {/* Dropzone */}
              <div
                onClick={() => amazonInputRef.current?.click()}
                className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-center cursor-pointer transition-colors ${
                  amazonFile
                    ? "border-emerald-400 bg-emerald-50/30"
                    : "border-slate-200 hover:border-slate-300 bg-slate-50/50"
                }`}
              >
                <UploadCloud className={`h-8 w-8 mb-2 ${amazonFile ? "text-emerald-600" : "text-slate-400"}`} />
                <p className="text-xs font-semibold text-slate-800">
                  {amazonFile ? amazonFile.name : "Click to select or drop your Amazon CSV"}
                </p>
                <p className="text-[10px] text-slate-400 mt-1">
                  Supports .csv or .txt Date Range Reports
                </p>
                <input
                  ref={amazonInputRef}
                  type="file"
                  accept=".csv,.txt"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files?.[0]) setAmazonFile(e.target.files[0]);
                  }}
                />
              </div>

              {amazonError && (
                <div className="flex items-center gap-2 rounded-lg bg-rose-50 p-3 text-xs text-rose-700">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{amazonError}</span>
                </div>
              )}

              {amazonResult && (
                <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-4 space-y-2 text-xs text-emerald-900">
                  <div className="flex items-center gap-2 font-bold text-emerald-800">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Report Processed Successfully!</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-emerald-200">
                    <div>Orders Imported: <strong className="font-mono">{amazonResult.orders_imported}</strong></div>
                    <div>Fees Extracted: <strong className="font-mono">{amazonResult.fees_extracted}</strong></div>
                    <div>Total Sales: <strong className="font-mono">₹{amazonResult.total_sales_value}</strong></div>
                    <div>SKUs Found: <strong className="font-mono">{amazonResult.skus_identified}</strong></div>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() => amazonFile && amazonMutation.mutate(amazonFile)}
              disabled={!amazonFile || amazonMutation.isPending}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-slate-900 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 disabled:opacity-50 transition-colors"
            >
              <FileSpreadsheet className="h-4 w-4" />
              <span>{amazonMutation.isPending ? "Parsing & Reconciling..." : "Process Amazon Report"}</span>
            </button>
          </div>

          {/* Card 2: Product Costs (COGS) CSV */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-600 font-bold text-white shadow-sm">
                    ₹
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-900">Product Costs (COGS) Sheet</h2>
                    <p className="text-[11px] text-slate-400">Supplier & Packaging Costs (.csv)</p>
                  </div>
                </div>
                <a
                  href={api.getSampleReportUrl("seller_cogs")}
                  download="seller_cogs_sample.csv"
                  className="flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-[11px] font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                  title="Download sample template"
                >
                  <Download className="h-3 w-3" />
                  <span>Sample</span>
                </a>
              </div>

              {/* Instructions */}
              <div className="rounded-lg bg-slate-50 p-3 text-[11px] text-slate-600 space-y-1">
                <p className="font-semibold text-slate-700">Required CSV Columns:</p>
                <p>• <strong>sku</strong>: Your merchant SKU (must match Amazon/Flipkart)</p>
                <p>• <strong>product_cost</strong>: Supplier purchase / manufacturing cost</p>
                <p>• <strong>packaging_cost</strong>: Boxes, bubble wrap, polybags</p>
                <p>• <strong>other_cost</strong>: Barcode stickers, inserts, quality check</p>
              </div>

              {/* Dropzone */}
              <div
                onClick={() => cogsInputRef.current?.click()}
                className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-center cursor-pointer transition-colors ${
                  cogsFile
                    ? "border-emerald-400 bg-emerald-50/30"
                    : "border-slate-200 hover:border-slate-300 bg-slate-50/50"
                }`}
              >
                <UploadCloud className={`h-8 w-8 mb-2 ${cogsFile ? "text-emerald-600" : "text-slate-400"}`} />
                <p className="text-xs font-semibold text-slate-800">
                  {cogsFile ? cogsFile.name : "Click to select or drop your COGS CSV"}
                </p>
                <p className="text-[10px] text-slate-400 mt-1">
                  Download the sample above if you need a template
                </p>
                <input
                  ref={cogsInputRef}
                  type="file"
                  accept=".csv,.txt"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files?.[0]) setCogsFile(e.target.files[0]);
                  }}
                />
              </div>

              {cogsError && (
                <div className="flex items-center gap-2 rounded-lg bg-rose-50 p-3 text-xs text-rose-700">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{cogsError}</span>
                </div>
              )}

              {cogsResult && (
                <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-4 space-y-2 text-xs text-emerald-900">
                  <div className="flex items-center gap-2 font-bold text-emerald-800">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>COGS Updated Successfully!</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-emerald-200">
                    <div>Products Updated: <strong className="font-mono">{cogsResult.products_updated}</strong></div>
                    <div>New SKUs Added: <strong className="font-mono">{cogsResult.products_created}</strong></div>
                    <div className="col-span-2">
                      Total SKUs Processed: <strong className="font-mono">{cogsResult.rows_processed}</strong>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() => cogsFile && cogsMutation.mutate(cogsFile)}
              disabled={!cogsFile || cogsMutation.isPending}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-slate-900 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 disabled:opacity-50 transition-colors"
            >
              <FileSpreadsheet className="h-4 w-4" />
              <span>{cogsMutation.isPending ? "Applying Costs..." : "Import Product Costs"}</span>
            </button>
          </div>
        </div>

        {/* Security & Idempotency Guarantee */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-600" />
            <h3 className="text-sm font-semibold text-slate-900">Idempotent Re-Import & Privacy Guarantee</h3>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            All reports are parsed directly into your isolated organization database. You can safely upload overlapping date range reports
            without worry: our synchronizer detects previously processed order IDs and avoids creating duplicate sales or double-counting marketplace fees.
          </p>
        </div>
      </main>
    </div>
  );
}
