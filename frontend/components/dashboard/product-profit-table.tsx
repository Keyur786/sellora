"use client";

import { useState } from "react";
import { ProductProfitItem } from "@/types";
import { formatINR, formatPercent } from "@/lib/utils";
import { ArrowUpDown, HelpCircle } from "lucide-react";

interface ProductProfitTableProps {
  products: ProductProfitItem[];
  isLoading?: boolean;
}

export function ProductProfitTable({ products, isLoading }: ProductProfitTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState<keyof ProductProfitItem>("net_profit");
  const [sortAsc, setSortAsc] = useState(false);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-48 bg-slate-200 rounded"></div>
          <div className="h-10 w-full bg-slate-100 rounded"></div>
          <div className="h-10 w-full bg-slate-100 rounded"></div>
          <div className="h-10 w-full bg-slate-100 rounded"></div>
        </div>
      </div>
    );
  }

  const filtered = products
    .filter(
      (p) =>
        p.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.sku.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      const valA = parseFloat(String(a[sortField] || 0));
      const valB = parseFloat(String(b[sortField] || 0));
      return sortAsc ? valA - valB : valB - valA;
    });

  const handleSort = (field: keyof ProductProfitItem) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Product Profitability Breakdown</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Unit economics including product acquisition, packaging, commission, logistics, and ad costs
          </p>
        </div>
        <div>
          <input
            type="text"
            placeholder="Search by SKU or title..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full sm:w-64 rounded-lg border border-slate-200 px-3 py-1.5 text-xs focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-slate-100 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider">
            <tr>
              <th className="py-3 px-4">Product & SKU</th>
              <th className="py-3 px-3 text-right">Units</th>
              <th className="py-3 px-3 text-right cursor-pointer" onClick={() => handleSort("gross_sales")}>
                <div className="flex items-center justify-end gap-1">
                  <span>Sales</span>
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="py-3 px-3 text-right">Product Cost</th>
              <th className="py-3 px-3 text-right">Mkt Fees</th>
              <th className="py-3 px-3 text-right">Ads</th>
              <th className="py-3 px-3 text-right">Returns</th>
              <th className="py-3 px-4 text-right cursor-pointer" onClick={() => handleSort("net_profit")}>
                <div className="flex items-center justify-end gap-1 text-emerald-700">
                  <span>Net Profit</span>
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="py-3 px-4 text-right cursor-pointer" onClick={() => handleSort("profit_margin_percentage")}>
                <div className="flex items-center justify-end gap-1">
                  <span>Margin</span>
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-8 text-center text-slate-400">
                  No matching products found.
                </td>
              </tr>
            ) : (
              filtered.map((item) => {
                const profitNum = parseFloat(String(item.net_profit));
                const isLoss = profitNum < 0;

                return (
                  <tr key={item.product_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900 max-w-xs truncate" title={item.title}>
                        {item.title}
                      </div>
                      <div className="font-mono text-[11px] text-slate-500">{item.sku}</div>
                    </td>
                    <td className="py-3 px-3 text-right font-medium">{item.units_sold}</td>
                    <td className="py-3 px-3 text-right font-semibold text-slate-900">
                      {formatINR(item.gross_sales)}
                    </td>
                    <td className="py-3 px-3 text-right text-slate-600">
                      {formatINR(parseFloat(String(item.product_cost)) + parseFloat(String(item.packaging_cost)))}
                    </td>
                    <td className="py-3 px-3 text-right text-slate-600">
                      {formatINR(parseFloat(String(item.marketplace_fees)) + parseFloat(String(item.shipping_cost)))}
                    </td>
                    <td className="py-3 px-3 text-right text-slate-600">{formatINR(item.advertising_cost)}</td>
                    <td className="py-3 px-3 text-right text-slate-600">{formatINR(item.returns_cost)}</td>
                    <td className="py-3 px-4 text-right font-bold">
                      <span className={isLoss ? "text-rose-600" : "text-emerald-700"}>
                        {formatINR(item.net_profit)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-semibold">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ${
                          isLoss ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-700"
                        }`}
                      >
                        {formatPercent(item.profit_margin_percentage)}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
