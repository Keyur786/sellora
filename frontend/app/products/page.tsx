"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import { Product } from "@/types";
import { Edit3, Check, X, Plus, Package, Loader2 } from "lucide-react";

export default function ProductsPage() {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editCost, setEditCost] = useState<string>("");
  const [editPackaging, setEditPackaging] = useState<string>("");
  const [editOther, setEditOther] = useState<string>("");

  const [isAddOpen, setIsAddOpen] = useState<boolean>(false);
  const [newProd, setNewProd] = useState({
    sku: "",
    title: "",
    asin_or_fsn: "",
    category: "",
    cost_price: 0,
    packaging_cost: 0,
    other_cost: 0,
    initial_stock: 0,
  });
  const [addError, setAddError] = useState<string | null>(null);

  const { data: products = [], isLoading } = useQuery({
    queryKey: ["products"],
    queryFn: () => api.getProducts(),
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof newProd) => api.createProduct(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setIsAddOpen(false);
      setNewProd({
        sku: "",
        title: "",
        asin_or_fsn: "",
        category: "",
        cost_price: 0,
        packaging_cost: 0,
        other_cost: 0,
        initial_stock: 0,
      });
      setAddError(null);
    },
    onError: (err: any) => {
      setAddError(err.message || "Failed to create product");
    },
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

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProd.sku.trim() || !newProd.title.trim()) {
      setAddError("SKU and Title are required.");
      return;
    }
    setAddError(null);
    createMutation.mutate(newProd);
  };

  return (
    <div className="flex-1 pb-12">
      <Header />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Products & Costs</h1>
            <p className="text-xs text-slate-500 mt-1">
              Manage product catalog, COGS, and packaging costs.
            </p>
          </div>
          <button
            onClick={() => {
              setAddError(null);
              setIsAddOpen(true);
            }}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-all"
          >
            <Plus className="h-4 w-4" />
            <span>Add Product</span>
          </button>
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

        {/* Add Product Modal */}
        {isAddOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg rounded-xl border border-slate-200 bg-white shadow-xl overflow-hidden animate-in fade-in zoom-in duration-150">
              <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
                <div className="flex items-center gap-2">
                  <Package className="h-5 w-5 text-emerald-600" />
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Add New Product</h3>
                    <p className="text-[11px] text-slate-500">Add a product listing and set initial COGS.</p>
                  </div>
                </div>
                <button
                  onClick={() => setIsAddOpen(false)}
                  className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleCreateSubmit} className="p-6 space-y-4 text-xs">
                {addError && (
                  <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs">
                    {addError}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">SKU *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. COPPER-BTL-1L"
                      value={newProd.sku}
                      onChange={(e) => setNewProd({ ...newProd, sku: e.target.value })}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-800 font-mono focus:border-emerald-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">ASIN / FSN</label>
                    <input
                      type="text"
                      placeholder="e.g. B08N5WRWNW"
                      value={newProd.asin_or_fsn}
                      onChange={(e) => setNewProd({ ...newProd, asin_or_fsn: e.target.value })}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-800 font-mono focus:border-emerald-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Product Title *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Pure Hammered Copper Water Bottle 1000ml"
                    value={newProd.title}
                    onChange={(e) => setNewProd({ ...newProd, title: e.target.value })}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-800 focus:border-emerald-500 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Category</label>
                    <input
                      type="text"
                      placeholder="e.g. Kitchen & Home"
                      value={newProd.category}
                      onChange={(e) => setNewProd({ ...newProd, category: e.target.value })}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-800 focus:border-emerald-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Initial Stock Units</label>
                    <input
                      type="number"
                      min="0"
                      placeholder="0"
                      value={newProd.initial_stock || ""}
                      onChange={(e) => setNewProd({ ...newProd, initial_stock: parseInt(e.target.value) || 0 })}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-800 focus:border-emerald-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg space-y-2.5">
                  <p className="font-bold text-slate-800">Unit Cost Breakdown (COGS)</p>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="text-[11px] text-slate-500 block mb-1">Cost Price (₹)</label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                        value={newProd.cost_price || ""}
                        onChange={(e) => setNewProd({ ...newProd, cost_price: parseFloat(e.target.value) || 0 })}
                        className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-right font-mono focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-500 block mb-1">Packaging (₹)</label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                        value={newProd.packaging_cost || ""}
                        onChange={(e) => setNewProd({ ...newProd, packaging_cost: parseFloat(e.target.value) || 0 })}
                        className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-right font-mono focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-500 block mb-1">Other Cost (₹)</label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                        value={newProd.other_cost || ""}
                        onChange={(e) => setNewProd({ ...newProd, other_cost: parseFloat(e.target.value) || 0 })}
                        className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-right font-mono focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-2 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setIsAddOpen(false)}
                    className="rounded-lg border border-slate-200 px-4 py-2 font-medium text-slate-600 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createMutation.isPending}
                    className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {createMutation.isPending ? (
                      <>
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        <span>Creating...</span>
                      </>
                    ) : (
                      <>
                        <Plus className="h-3.5 w-3.5" />
                        <span>Save Product</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

