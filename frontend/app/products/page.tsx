"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import { Product } from "@/types";
import { Edit3, Check, X, Plus, Package } from "lucide-react";

export default function ProductsPage() {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editCost, setEditCost] = useState<string>("");
  const [editPackaging, setEditPackaging] = useState<string>("");
  const [editOther, setEditOther] = useState<string>("");

  const { data: products = [], isLoading } = useQuery({
    queryKey: ["products"],
    queryFn: () => api.getProducts(),
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      costs,
    }: {
      id: string;
      costs: { cost_price: number; packaging_cost: number; other_cost: number };
    }) => api.updateProductCOGS(id, costs),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setEditingId(null);
    },
  });

  const startEdit = (p: Product) => {
    setEditingId(p.id);
    setEditCost(String(p.cost_price));
    setEditPackaging(String(p.packaging_cost));
    setEditOther(String(p.other_cost));
  };

  const saveEdit = (id: string) => {
    updateMutation.mutate({
      id,
      costs: {
        cost_price: parseFloat(editCost) || 0,
        packaging_cost: parseFloat(editPackaging) || 0,
        other_cost: parseFloat(editOther) || 0,
      },
    });
  };

  return (
    <div className="flex-1 pb-12">
      <Header />

      <main className="px-8 py-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Products & Cost Configuration</h1>
            <p className="text-xs text-slate-500 mt-1">
              Set unit product acquisition cost, packaging materials, and additional expenses for accurate profit calculations.
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-100 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Product</th>
                  <th className="py-3 px-3">SKU</th>
                  <th className="py-3 px-3">Identifier</th>
                  <th className="py-3 px-3 text-right">Available Stock</th>
                  <th className="py-3 px-3 text-right">Product Cost</th>
                  <th className="py-3 px-3 text-right">Packaging Cost</th>
                  <th className="py-3 px-3 text-right">Other Unit Cost</th>
                  <th className="py-3 px-3 text-right">Total Unit COGS</th>
                  <th className="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {isLoading ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-slate-400">
                      Loading product catalog...
                    </td>
                  </tr>
                ) : products.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-slate-400">
                      No products found. Connect a marketplace to import products.
                    </td>
                  </tr>
                ) : (
                  products.map((p) => {
                    const isEditing = editingId === p.id;
                    const totalUnitCost =
                      parseFloat(String(p.cost_price)) +
                      parseFloat(String(p.packaging_cost)) +
                      parseFloat(String(p.other_cost));

                    return (
                      <tr key={p.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3 px-4">
                          <div className="font-semibold text-slate-900 max-w-xs truncate">{p.title}</div>
                          <div className="text-[11px] text-slate-400">{p.category || "General"}</div>
                        </td>
                        <td className="py-3 px-3 font-mono font-medium text-slate-700">{p.sku}</td>
                        <td className="py-3 px-3 font-mono text-[11px] text-slate-500">{p.asin_or_fsn || "-"}</td>
                        <td className="py-3 px-3 text-right font-medium">{p.available_stock}</td>

                        {/* Product Cost */}
                        <td className="py-3 px-3 text-right">
                          {isEditing ? (
                            <input
                              type="number"
                              step="0.01"
                              value={editCost}
                              onChange={(e) => setEditCost(e.target.value)}
                              className="w-20 rounded border border-emerald-500 px-2 py-1 text-right text-xs focus:outline-none"
                            />
                          ) : (
                            <span className="font-semibold">{formatINR(p.cost_price)}</span>
                          )}
                        </td>

                        {/* Packaging Cost */}
                        <td className="py-3 px-3 text-right">
                          {isEditing ? (
                            <input
                              type="number"
                              step="0.01"
                              value={editPackaging}
                              onChange={(e) => setEditPackaging(e.target.value)}
                              className="w-20 rounded border border-emerald-500 px-2 py-1 text-right text-xs focus:outline-none"
                            />
                          ) : (
                            <span>{formatINR(p.packaging_cost)}</span>
                          )}
                        </td>

                        {/* Other Cost */}
                        <td className="py-3 px-3 text-right">
                          {isEditing ? (
                            <input
                              type="number"
                              step="0.01"
                              value={editOther}
                              onChange={(e) => setEditOther(e.target.value)}
                              className="w-20 rounded border border-emerald-500 px-2 py-1 text-right text-xs focus:outline-none"
                            />
                          ) : (
                            <span>{formatINR(p.other_cost)}</span>
                          )}
                        </td>

                        {/* Total COGS */}
                        <td className="py-3 px-3 text-right font-bold text-slate-900">
                          {formatINR(totalUnitCost)}
                        </td>

                        {/* Actions */}
                        <td className="py-3 px-4 text-center">
                          {isEditing ? (
                            <div className="flex items-center justify-center gap-1.5">
                              <button
                                onClick={() => saveEdit(p.id)}
                                disabled={updateMutation.isPending}
                                className="rounded p-1 text-emerald-600 hover:bg-emerald-50"
                                title="Save costs"
                              >
                                <Check className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => setEditingId(null)}
                                className="rounded p-1 text-slate-400 hover:bg-slate-100"
                                title="Cancel"
                              >
                                <X className="h-4 w-4" />
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => startEdit(p)}
                              className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-[11px] font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                            >
                              <Edit3 className="h-3 w-3" />
                              <span>Edit COGS</span>
                            </button>
                          )}
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
