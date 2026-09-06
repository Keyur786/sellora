"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { formatINR, formatDate } from "@/lib/utils";

export default function OrdersPage() {
  const [marketplace, setMarketplace] = useState<string>("");
  const [page, setPage] = useState<number>(1);

  const { data, isLoading } = useQuery({
    queryKey: ["orders", page, marketplace],
    queryFn: () => api.getOrders(page, 20, marketplace || undefined),
  });

  const orders = data?.orders || [];
  const totalCount = data?.total_count || 0;

  return (
    <div className="flex-1 pb-12">
      <Header />

      <main className="px-8 py-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Orders Ledger</h1>
            <p className="text-xs text-slate-500 mt-1">
              Complete multichannel order stream with fees, fulfillment channels, and customer locations.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setMarketplace("")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                marketplace === ""
                  ? "bg-slate-900 text-white"
                  : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
              }`}
            >
              All Marketplaces
            </button>
            <button
              onClick={() => setMarketplace("amazon")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                marketplace === "amazon"
                  ? "bg-amber-600 text-white"
                  : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
              }`}
            >
              Amazon India
            </button>
            <button
              onClick={() => setMarketplace("flipkart")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                marketplace === "flipkart"
                  ? "bg-blue-600 text-white"
                  : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
              }`}
            >
              Flipkart
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-100 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Marketplace Order ID</th>
                  <th className="py-3 px-3">Marketplace</th>
                  <th className="py-3 px-3">Date</th>
                  <th className="py-3 px-3">Fulfillment</th>
                  <th className="py-3 px-3">Location</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-4 text-right">Order Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-400">
                      Loading orders...
                    </td>
                  </tr>
                ) : orders.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-400">
                      No orders found for the selected filter.
                    </td>
                  </tr>
                ) : (
                  orders.map((o) => {
                    const isAmazon = o.marketplace_type.toLowerCase() === "amazon";
                    return (
                      <tr key={o.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3 px-4 font-mono font-semibold text-slate-900">
                          {o.marketplace_order_id}
                        </td>
                        <td className="py-3 px-3">
                          <span
                            className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                              isAmazon
                                ? "bg-amber-50 text-amber-800 border border-amber-200"
                                : "bg-blue-50 text-blue-800 border border-blue-200"
                            }`}
                          >
                            {isAmazon ? "Amazon.in" : "Flipkart"}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-slate-500">{formatDate(o.order_date)}</td>
                        <td className="py-3 px-3 font-medium text-slate-600">
                          {o.fulfillment_channel || "Standard"}
                        </td>
                        <td className="py-3 px-3 text-slate-600">
                          {o.customer_city ? `${o.customer_city}, ${o.customer_state || ""}` : "India"}
                        </td>
                        <td className="py-3 px-3">
                          <span className="inline-flex rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                            {o.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right font-bold text-slate-900">
                          {formatINR(o.total_amount)}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
