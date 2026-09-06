"use client";

import { Order } from "@/types";
import { formatINR, formatDate } from "@/lib/utils";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

interface RecentOrdersProps {
  orders: Order[];
}

export function RecentOrders({ orders }: RecentOrdersProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Recent Marketplace Orders</h2>
          <p className="text-xs text-slate-500 mt-0.5">Real-time sync from Amazon India & Flipkart</p>
        </div>
        <Link
          href="/orders"
          className="flex items-center gap-1 text-xs font-medium text-emerald-700 hover:text-emerald-800"
        >
          <span>View All</span>
          <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-slate-100 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider">
            <tr>
              <th className="py-2.5 px-3">Order ID</th>
              <th className="py-2.5 px-3">Marketplace</th>
              <th className="py-2.5 px-3">Date</th>
              <th className="py-2.5 px-3">Customer</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3 text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {orders.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-6 text-center text-slate-400">
                  No orders recorded yet.
                </td>
              </tr>
            ) : (
              orders.map((order) => {
                const isAmazon = order.marketplace_type.toLowerCase() === "amazon";
                return (
                  <tr key={order.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-2.5 px-3 font-mono font-medium text-slate-900">
                      {order.marketplace_order_id}
                    </td>
                    <td className="py-2.5 px-3">
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
                    <td className="py-2.5 px-3 text-slate-500">{formatDate(order.order_date)}</td>
                    <td className="py-2.5 px-3 text-slate-600">
                      {order.customer_city ? `${order.customer_city}, ${order.customer_state || ""}` : "India"}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="inline-flex rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                        {order.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right font-semibold text-slate-900">
                      {formatINR(order.total_amount)}
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
