"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { formatINR, formatDate } from "@/lib/utils";
import {
  Truck,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Sparkles,
  Info,
  X,
  Receipt,
  Eye,
} from "lucide-react";
import { RTORiskResponse, Order } from "@/types";

export default function OrdersPage() {
  const [marketplace, setMarketplace] = useState<string>("");
  const [page, setPage] = useState<number>(1);
  const [selectedRiskOrder, setSelectedRiskOrder] = useState<RTORiskResponse | null>(null);
  const [selectedOrderDetail, setSelectedOrderDetail] = useState<Order | null>(null);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false);

  const { data, isLoading } = useQuery({
    queryKey: ["orders", page, marketplace],
    queryFn: () => api.getOrders(page, 20, marketplace || undefined),
  });

  const { data: rtoSummary } = useQuery({
    queryKey: ["ordersRTOSummary"],
    queryFn: () => api.getOrdersRTOSummary(50),
  });

  const orders = data?.orders || [];
  const riskMap = new Map<string, RTORiskResponse>();
  if (rtoSummary?.orders) {
    for (const r of rtoSummary.orders) {
      riskMap.set(r.order_id, r);
    }
  }

  const handleOpenDetail = async (order: Order) => {
    try {
      setLoadingDetail(true);
      setSelectedOrderDetail(order);
      const full = await api.getOrder(order.id);
      setSelectedOrderDetail(full);
    } catch {
      setSelectedOrderDetail(order);
    } finally {
      setLoadingDetail(false);
    }
  };

  return (
    <div className="flex-1 pb-16">
      <Header />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-7xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Orders</h1>
            <p className="text-xs text-slate-500 mt-1">
              Order stream, fees, and doorstep delivery risk.
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

        {/* Predictive COD RTO Summary Bar */}
        {rtoSummary && (
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="space-y-0.5">
              <p className="text-slate-500 font-medium">Orders Evaluated</p>
              <p className="text-base font-bold text-slate-900">{rtoSummary.total_orders_evaluated}</p>
            </div>
            <div className="space-y-0.5">
              <p className="text-slate-500 font-medium">High Doorstep Risk</p>
              <p className="text-base font-bold text-rose-600 flex items-center gap-1">
                <span>{rtoSummary.high_risk_count} COD Orders</span>
              </p>
            </div>
            <div className="space-y-0.5">
              <p className="text-slate-500 font-medium">Potential Freight at Risk</p>
              <p className="text-base font-bold text-amber-700 font-mono">
                {formatINR(rtoSummary.potential_rto_loss_at_risk)}
              </p>
            </div>
            <div className="space-y-0.5">
              <p className="text-slate-500 font-medium">Safe / Low Risk</p>
              <p className="text-base font-bold text-emerald-600">{rtoSummary.low_risk_count} Orders</p>
            </div>
          </div>
        )}

        {/* Orders Table */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-100 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Marketplace Order ID</th>
                  <th className="py-3 px-3">Marketplace</th>
                  <th className="py-3 px-3">Date</th>
                  <th className="py-3 px-3">Location</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-right">Order Total</th>
                  <th className="py-3 px-4 text-center">COD RTO Risk</th>
                  <th className="py-3 px-3 text-center">Fee Breakdown</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-400">
                      Loading orders...
                    </td>
                  </tr>
                ) : orders.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-400">
                      No orders found for the selected filter.
                    </td>
                  </tr>
                ) : (
                  orders.map((o) => {
                    const isAmazon = o.marketplace_type.toLowerCase() === "amazon";
                    const risk = riskMap.get(o.id);
                    return (
                      <tr key={o.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3 px-4 font-mono font-semibold text-slate-900">
                          <button
                            onClick={() => handleOpenDetail(o)}
                            className="hover:text-emerald-600 hover:underline transition-colors text-left font-mono"
                          >
                            {o.marketplace_order_id}
                          </button>
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
                        <td className="py-3 px-3 text-slate-600">
                          {o.customer_city ? `${o.customer_city}, ${o.customer_state || ""}` : "India"}
                        </td>
                        <td className="py-3 px-3">
                          <span className="inline-flex rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                            {o.status}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-right font-bold text-slate-900 font-mono">
                          {formatINR(o.total_amount)}
                        </td>
                        <td className="py-3 px-4 text-center">
                          {risk ? (
                            <button
                              onClick={() => setSelectedRiskOrder(risk)}
                              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold transition-transform hover:scale-105 ${
                                risk.risk_level === "High"
                                  ? "bg-rose-100 text-rose-800 border border-rose-200"
                                  : risk.risk_level === "Medium"
                                  ? "bg-amber-100 text-amber-800 border border-amber-200"
                                  : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                              }`}
                            >
                              <span>{risk.risk_level} Risk ({risk.risk_score}%)</span>
                            </button>
                          ) : (
                            <span className="text-slate-400 text-[11px]">—</span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-center">
                          <button
                            onClick={() => handleOpenDetail(o)}
                            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-colors"
                          >
                            <Receipt className="h-3 w-3 text-emerald-600" />
                            <span>Fees & Net</span>
                          </button>
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

      {/* Order Financial Drill-Down Modal */}
      {selectedOrderDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl rounded-xl border border-slate-200 bg-white shadow-xl overflow-hidden animate-in fade-in zoom-in duration-150">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
              <div className="flex items-center gap-2.5">
                <Receipt className="h-5 w-5 text-emerald-600" />
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Order Financial Statement</h3>
                  <p className="text-[11px] text-slate-500 font-mono">
                    {selectedOrderDetail.marketplace_order_id} • {formatDate(selectedOrderDetail.order_date)}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedOrderDetail(null)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-5 text-xs max-h-[80vh] overflow-y-auto">
              {/* Top Financial Summary Cards */}
              {(() => {
                const totalGross = Number(selectedOrderDetail.total_amount || 0);
                const totalFees = (selectedOrderDetail.fees || []).reduce(
                  (acc, f) => acc + Number(f.amount || 0),
                  0
                );
                const netSettlement = totalGross - totalFees;

                return (
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">Gross Buyer Paid</span>
                      <p className="text-base font-bold text-slate-900 font-mono mt-0.5">{formatINR(totalGross)}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-rose-50 border border-rose-100">
                      <span className="text-[10px] text-rose-700 uppercase font-semibold">Marketplace Fees</span>
                      <p className="text-base font-bold text-rose-700 font-mono mt-0.5">-{formatINR(totalFees)}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200">
                      <span className="text-[10px] text-emerald-700 uppercase font-semibold">Net Payout</span>
                      <p className="text-base font-bold text-emerald-700 font-mono mt-0.5">{formatINR(netSettlement)}</p>
                    </div>
                  </div>
                );
              })()}

              {/* Order Meta & Destination */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-3 rounded-lg bg-slate-50/70 border border-slate-100 text-[11px]">
                <div>
                  <span className="text-slate-400">Marketplace:</span>
                  <p className="font-semibold text-slate-800 capitalize">
                    {selectedOrderDetail.marketplace_type} {selectedOrderDetail.fulfillment_channel ? `(${selectedOrderDetail.fulfillment_channel})` : ""}
                  </p>
                </div>
                <div>
                  <span className="text-slate-400">Delivery Status:</span>
                  <p className="font-semibold text-emerald-700">{selectedOrderDetail.status}</p>
                </div>
                <div>
                  <span className="text-slate-400">Destination:</span>
                  <p className="font-semibold text-slate-800">
                    {selectedOrderDetail.customer_city ? `${selectedOrderDetail.customer_city}, ${selectedOrderDetail.customer_state || ""}` : "India"}
                  </p>
                </div>
              </div>

              {/* Items in this order */}
              <div className="space-y-2">
                <p className="font-bold text-slate-800">Purchased Items</p>
                <div className="border border-slate-100 rounded-lg overflow-hidden divide-y divide-slate-100">
                  {selectedOrderDetail.items && selectedOrderDetail.items.length > 0 ? (
                    selectedOrderDetail.items.map((item) => (
                      <div key={item.id} className="p-3 flex items-center justify-between">
                        <div>
                          <p className="font-medium text-slate-900">{item.title}</p>
                          <p className="text-[10px] text-slate-400 font-mono">SKU: {item.sku} • Qty: {item.quantity}</p>
                        </div>
                        <span className="font-bold font-mono text-slate-900">{formatINR(item.item_price)}</span>
                      </div>
                    ))
                  ) : (
                    <p className="p-3 text-slate-400 text-center">No line item data available.</p>
                  )}
                </div>
              </div>

              {/* Itemized Fees Breakdown */}
              <div className="space-y-2">
                <p className="font-bold text-slate-800">Itemized Marketplace Deductions</p>
                {selectedOrderDetail.fees && selectedOrderDetail.fees.length > 0 ? (
                  <div className="border border-slate-100 rounded-lg overflow-hidden">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 border-b border-slate-100 text-slate-500">
                        <tr>
                          <th className="py-2 px-3 font-medium">Fee Category</th>
                          <th className="py-2 px-3 font-medium text-right">Deduction</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {selectedOrderDetail.fees.map((fee) => (
                          <tr key={fee.id}>
                            <td className="py-2 px-3 text-slate-700">
                              <span className="font-medium">{fee.fee_type}</span>
                              {fee.description && (
                                <span className="text-slate-400 block text-[10px]">{fee.description}</span>
                              )}
                            </td>
                            <td className="py-2 px-3 text-right font-mono font-medium text-rose-700">
                              -{formatINR(fee.amount)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="p-3 bg-slate-50 rounded-lg text-slate-500 text-center">
                    Marketplace settlement fee report not yet received for this order.
                  </p>
                )}
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => setSelectedOrderDetail(null)}
                  className="rounded-lg bg-slate-900 px-4 py-2 font-semibold text-white hover:bg-slate-800"
                >
                  Close Statement
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* RTO Risk Detail Modal */}
      {selectedRiskOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white shadow-xl overflow-hidden animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
              <div className="flex items-center gap-2">
                <Truck className="h-5 w-5 text-slate-700" />
                <div>
                  <h3 className="text-sm font-bold text-slate-900">COD Doorstep Risk Assessment</h3>
                  <p className="text-[11px] text-slate-500 font-mono">Order #{selectedRiskOrder.marketplace_order_id}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedRiskOrder(null)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              <div className="flex items-center justify-between bg-slate-50 p-3 rounded-lg border border-slate-100">
                <div>
                  <span className="text-slate-500">Calculated RTO Probability</span>
                  <p className="text-base font-bold text-slate-900">{selectedRiskOrder.risk_score}%</p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 font-bold ${
                    selectedRiskOrder.risk_level === "High"
                      ? "bg-rose-100 text-rose-800 border border-rose-200"
                      : selectedRiskOrder.risk_level === "Medium"
                      ? "bg-amber-100 text-amber-800 border border-amber-200"
                      : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                  }`}
                >
                  {selectedRiskOrder.risk_level} Risk
                </span>
              </div>

              {/* Risk Reasons */}
              <div className="space-y-1.5">
                <p className="font-bold text-slate-700">Risk Factor Signals:</p>
                <div className="space-y-1">
                  {selectedRiskOrder.risk_reasons.map((r, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-slate-600">
                      <span className="text-rose-500 font-bold">•</span>
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommended Mitigation */}
              <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 space-y-1">
                <p className="font-bold text-emerald-950 flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
                  <span>Recommended Action:</span>
                </p>
                <p className="text-emerald-900 leading-relaxed">{selectedRiskOrder.recommended_mitigation}</p>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => setSelectedRiskOrder(null)}
                  className="rounded-lg bg-slate-900 px-4 py-2 font-semibold text-white hover:bg-slate-800"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

