"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { MetricCard } from "@/components/dashboard/metric-card";
import { api } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import {
  Receipt,
  Plus,
  Trash2,
  Building2,
  Calendar,
  X,
  CreditCard,
  Repeat,
  DollarSign,
  PieChart,
  Lightbulb,
} from "lucide-react";

const PRESET_CATEGORIES = [
  "Warehouse & Godown Rent",
  "Warehouse & Packing Staff",
  "Packaging Materials & Boxes",
  "Software & SaaS Subscriptions",
  "CA & Tax Audit Retainer",
  "Office Utilities & Electricity",
  "Logistics & Direct Freight",
  "Marketing & Influencer Collabs",
  "Other Operational Overhead",
];

const PAYMENT_METHODS = [
  "Bank Transfer (NEFT/RTGS/IMPS)",
  "UPI / QR Code",
  "Business Credit Card",
  "Cheque",
  "Cash",
];

export default function ExpensesPage() {
  const queryClient = useQueryClient();
  const [days, setDays] = useState(90);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State
  const [formCategory, setFormCategory] = useState(PRESET_CATEGORIES[0]);
  const [formAmount, setFormAmount] = useState("");
  const [formDate, setFormDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [formVendor, setFormVendor] = useState("");
  const [formPaymentMethod, setFormPaymentMethod] = useState(PAYMENT_METHODS[0]);
  const [formIsRecurring, setFormIsRecurring] = useState(false);
  const [formDescription, setFormDescription] = useState("");
  const [formError, setFormError] = useState("");

  // Queries
  const { data: expenses = [], isLoading: isLoadingExpenses } = useQuery({
    queryKey: ["expenses", days, selectedCategory],
    queryFn: () => api.getExpenses(days, selectedCategory || undefined),
  });

  const { data: summary, isLoading: isLoadingSummary } = useQuery({
    queryKey: ["expenseSummary", days],
    queryFn: () => api.getExpenseSummary(days),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: api.createExpense,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      queryClient.invalidateQueries({ queryKey: ["expenseSummary"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setIsModalOpen(false);
      resetForm();
    },
    onError: (err: any) => {
      setFormError(err.message || "Failed to save expense. Please try again.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteExpense,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      queryClient.invalidateQueries({ queryKey: ["expenseSummary"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const resetForm = () => {
    setFormCategory(PRESET_CATEGORIES[0]);
    setFormAmount("");
    setFormDate(new Date().toISOString().split("T")[0]);
    setFormVendor("");
    setFormPaymentMethod(PAYMENT_METHODS[0]);
    setFormIsRecurring(false);
    setFormDescription("");
    setFormError("");
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const amountNum = parseFloat(formAmount);
    if (!amountNum || amountNum <= 0) {
      setFormError("Please enter a valid amount greater than ₹0.");
      return;
    }
    setFormError("");
    createMutation.mutate({
      category: formCategory,
      amount: amountNum,
      currency: "INR",
      date: formDate,
      vendor_name: formVendor.trim() || undefined,
      payment_method: formPaymentMethod,
      is_recurring: formIsRecurring,
      description: formDescription.trim() || undefined,
    });
  };

  const handleDelete = (id: string, description?: string) => {
    if (confirm(`Are you sure you want to delete this expense record${description ? ` ("${description}")` : ""}?`)) {
      deleteMutation.mutate(id);
    }
  };

  const topCategory = summary?.categories && summary.categories.length > 0 ? summary.categories[0] : null;
  const recurringCount = expenses.filter((e) => e.is_recurring).length;
  const totalAmountNum = Number(summary?.total_expenses || 0);
  const dailyAverage = days > 0 ? totalAmountNum / days : 0;

  return (
    <div className="flex-1 pb-16">
      <Header days={days} onDaysChange={setDays} />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-7xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Expenses
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Operating expenses, warehouse overhead, and recurring costs.
            </p>
          </div>
          <button
            onClick={() => {
              resetForm();
              setIsModalOpen(true);
            }}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-emerald-500 transition-colors self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            <span>Add Expense</span>
          </button>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title={`Total OPEX (${days} Days)`}
            value={formatINR(summary?.total_expenses || 0)}
            subtext={`${expenses.length} logged expense entries`}
            icon={Receipt}
            variant="default"
          />

          <MetricCard
            title="Top Spending Category"
            value={topCategory ? topCategory.category : "None"}
            subtext={topCategory ? `${formatINR(topCategory.total_amount)} (${topCategory.percentage}% of OPEX)` : "No expenses"}
            icon={Building2}
            variant="warning"
          />

          <MetricCard
            title="Recurring Commitments"
            value={`${recurringCount} Active`}
            subtext="Monthly rent, salaries & tools"
            icon={Repeat}
            variant="default"
          />

          <MetricCard
            title="Daily Overhead Burn"
            value={formatINR(dailyAverage)}
            subtext="Fixed daily cost to operate store"
            icon={DollarSign}
            variant="default"
          />
        </div>

        {/* Main Grid: Left Table (2 cols), Right Breakdown (1 col) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Expenses Table (2 cols) */}
          <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden flex flex-col justify-between">
            <div>
              <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">Expense Ledger</h2>
                  <p className="text-[11px] text-slate-500">Itemized overhead deductions impacting your store's net profit</p>
                </div>

                {/* Filter by Category */}
                <div className="flex items-center gap-2">
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="rounded-lg border border-slate-200 bg-slate-50/50 px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="">All Categories</option>
                    {PRESET_CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-100 bg-slate-50/75 text-slate-500 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Date</th>
                      <th className="py-3 px-3">Category & Notes</th>
                      <th className="py-3 px-3">Vendor / Payee</th>
                      <th className="py-3 px-3">Payment</th>
                      <th className="py-3 px-4 text-right">Amount</th>
                      <th className="py-3 px-3 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {isLoadingExpenses ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-slate-400">
                          Loading business expenses...
                        </td>
                      </tr>
                    ) : expenses.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-12 text-center text-slate-400 space-y-2">
                          <Receipt className="h-8 w-8 text-slate-300 mx-auto" />
                          <p className="font-medium text-slate-500">No expenses recorded for this period</p>
                          <p className="text-[11px]">Click "Log Business Expense" to factor in warehouse rent, staff, or tools.</p>
                        </td>
                      </tr>
                    ) : (
                      expenses.map((exp) => (
                        <tr key={exp.id} className="hover:bg-slate-50/80 transition-colors">
                          <td className="py-3 px-4 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                            {exp.date}
                          </td>
                          <td className="py-3 px-3">
                            <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                              <span>{exp.category}</span>
                              {exp.is_recurring && (
                                <span className="inline-flex items-center rounded-full bg-blue-50 px-1.5 py-0.2 text-[9px] font-medium text-blue-700 border border-blue-200">
                                  Recurring
                                </span>
                              )}
                            </div>
                            {exp.description && (
                              <p className="text-[11px] text-slate-500 max-w-xs truncate">{exp.description}</p>
                            )}
                          </td>
                          <td className="py-3 px-3 text-slate-700 font-medium whitespace-nowrap">
                            {exp.vendor_name || "—"}
                          </td>
                          <td className="py-3 px-3 text-slate-500 text-[11px] whitespace-nowrap">
                            {exp.payment_method || "Direct"}
                          </td>
                          <td className="py-3 px-4 text-right font-bold text-slate-900 font-mono">
                            {formatINR(exp.amount)}
                          </td>
                          <td className="py-3 px-3 text-center">
                            <button
                              onClick={() => handleDelete(exp.id, exp.description)}
                              className="rounded p-1 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition-colors"
                              title="Delete Expense"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right Column: Category Distribution & Advice (1 col) */}
          <div className="space-y-6">
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">OPEX Category Distribution</h2>
                  <p className="text-[11px] text-slate-500">Proportion of business overheads by type</p>
                </div>
                <PieChart className="h-4 w-4 text-slate-400" />
              </div>

              <div className="space-y-3 pt-2">
                {!summary?.categories || summary.categories.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-6">No expenses categorized yet.</p>
                ) : (
                  summary.categories.map((cat, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-slate-700 truncate max-w-[190px]">{cat.category}</span>
                        <span className="font-semibold text-slate-900">
                          {cat.percentage}% ({formatINR(cat.total_amount)})
                        </span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-emerald-500 transition-all"
                          style={{ width: `${Math.min(100, cat.percentage)}%` }}
                        ></div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Indian Seller Overhead Guide Card */}
            <div className="rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-emerald-50/40 p-5 space-y-2.5">
              <div className="flex items-center gap-2 text-emerald-800 text-xs font-bold">
                <Lightbulb className="h-4 w-4 text-emerald-600" />
                <span>Why Offline OPEX Matters</span>
              </div>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                Marketplace settlement reports only show commissions and courier charges. If your business spends ₹25,000/month
                on warehouse rent, ₹18,000 on packing labor, and ₹8,000 on corrugated boxes, your actual bank account may be
                losing money even if Amazon Seller Central shows a positive disbursement!
              </p>
              <div className="pt-1 text-[11px] text-emerald-700 font-semibold">
                ✓ Log all recurring rent and staff expenses to reveal true cashflow.
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Log Expense Modal Dialog */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-slate-200 bg-white shadow-xl overflow-hidden animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Log Operating Expense</h3>
                <p className="text-xs text-slate-500">Record a non-marketplace business cost</p>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="p-6 space-y-4">
              {formError && (
                <div className="rounded-lg bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700">
                  {formError}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Category */}
                <div className="sm:col-span-2 space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Expense Category *</label>
                  <select
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    required
                  >
                    {PRESET_CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Amount */}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Amount (₹) *</label>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-xs font-bold text-slate-400">₹</span>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="5000.00"
                      value={formAmount}
                      onChange={(e) => setFormAmount(e.target.value)}
                      className="w-full rounded-lg border border-slate-200 pl-7 pr-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      required
                    />
                  </div>
                </div>

                {/* Date */}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Date *</label>
                  <input
                    type="date"
                    value={formDate}
                    onChange={(e) => setFormDate(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    required
                  />
                </div>

                {/* Vendor / Payee */}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Vendor / Payee Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Mahavir Box Suppliers"
                    value={formVendor}
                    onChange={(e) => setFormVendor(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                {/* Payment Method */}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Payment Mode</label>
                  <select
                    value={formPaymentMethod}
                    onChange={(e) => setFormPaymentMethod(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    {PAYMENT_METHODS.map((method) => (
                      <option key={method} value={method}>
                        {method}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Description */}
                <div className="sm:col-span-2 space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Description / Bill Notes</label>
                  <input
                    type="text"
                    placeholder="e.g. 1000 corrugated 3-ply boxes (size 8x6x4) + 5 rolls brown tape"
                    value={formDescription}
                    onChange={(e) => setFormDescription(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                {/* Recurring Checkbox */}
                <div className="sm:col-span-2 flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="isRecurring"
                    checked={formIsRecurring}
                    onChange={(e) => setFormIsRecurring(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <label htmlFor="isRecurring" className="text-xs font-medium text-slate-700 cursor-pointer">
                    Monthly recurring expense (e.g. rent, salaries, software)
                  </label>
                </div>
              </div>

              {/* Form Buttons */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-emerald-500 transition-colors disabled:opacity-50"
                >
                  {createMutation.isPending ? "Saving..." : "Save Expense"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

