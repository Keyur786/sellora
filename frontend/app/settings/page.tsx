"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/header";
import { Building2, Shield, Check, Loader2, Save, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { Organization } from "@/types";

export default function SettingsPage() {
  const [org, setOrg] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    currency: "INR",
    timezone: "Asia/Kolkata",
  });
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    async function loadOrg() {
      try {
        setLoading(true);
        const data = await api.getOrganization();
        setOrg(data);
        setFormData({
          name: data.name || "",
          currency: data.currency || "INR",
          timezone: data.timezone || "Asia/Kolkata",
        });
      } catch (err: any) {
        console.error("Failed to load organization settings", err);
        setStatusMsg({ type: "error", text: "Failed to load store profile." });
      } finally {
        setLoading(false);
      }
    }
    loadOrg();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setStatusMsg({ type: "error", text: "Store name cannot be empty." });
      return;
    }

    try {
      setSaving(true);
      setStatusMsg(null);
      const updated = await api.updateOrganization({
        name: formData.name.trim(),
        currency: formData.currency,
        timezone: formData.timezone,
      });
      setOrg(updated);
      setStatusMsg({ type: "success", text: "Settings saved successfully." });
    } catch (err: any) {
      console.error("Failed to update organization", err);
      setStatusMsg({ type: "error", text: err.message || "Failed to update settings." });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-1 pb-12">
      <Header />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-4xl">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Organization Settings</h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage your store details, base currency, and tenant configuration.
          </p>
        </div>

        {statusMsg && (
          <div
            className={`p-3.5 rounded-xl border text-xs flex items-center gap-2.5 transition-all ${
              statusMsg.type === "success"
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : "bg-rose-50 border-rose-200 text-rose-800"
            }`}
          >
            {statusMsg.type === "success" ? (
              <Check className="h-4 w-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
            )}
            <span>{statusMsg.text}</span>
          </div>
        )}

        {/* Store Details Card */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-emerald-600" />
              <h2 className="text-base font-semibold text-slate-900">Store Profile</h2>
            </div>
            {org?.slug && (
              <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                Tenant: {org.slug}
              </span>
            )}
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-10 text-slate-400 gap-2 text-xs">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading store configuration...</span>
            </div>
          ) : (
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="font-medium text-slate-700 block mb-1.5">
                    Store / Organization Name
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors"
                    placeholder="e.g. Apex Retail India"
                  />
                </div>

                <div>
                  <label className="font-medium text-slate-700 block mb-1.5">
                    Tenant Slug (Internal ID)
                  </label>
                  <input
                    type="text"
                    disabled
                    value={org?.slug || org?.id || "demo-seller-india"}
                    className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-slate-500 cursor-not-allowed"
                  />
                </div>

                <div>
                  <label className="font-medium text-slate-700 block mb-1.5">Base Currency</label>
                  <select
                    value={formData.currency}
                    onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors"
                  >
                    <option value="INR">INR (₹) - Indian Rupee</option>
                    <option value="USD">USD ($) - US Dollar</option>
                    <option value="EUR">EUR (€) - Euro</option>
                    <option value="GBP">GBP (£) - British Pound</option>
                    <option value="AED">AED (د.إ) - UAE Dirham</option>
                  </select>
                </div>

                <div>
                  <label className="font-medium text-slate-700 block mb-1.5">Operational Timezone</label>
                  <select
                    value={formData.timezone}
                    onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors"
                  >
                    <option value="Asia/Kolkata">Asia/Kolkata (IST +5:30)</option>
                    <option value="Asia/Dubai">Asia/Dubai (GST +4:00)</option>
                    <option value="UTC">UTC (+0:00)</option>
                    <option value="America/New_York">America/New_York (EST -5:00)</option>
                    <option value="Europe/London">Europe/London (GMT +0:00)</option>
                  </select>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-all disabled:opacity-50"
                >
                  {saving ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <Save className="h-3.5 w-3.5" />
                      <span>Save Changes</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Security & Multi-tenancy */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Shield className="h-5 w-5 text-emerald-600" />
            <h2 className="text-base font-semibold text-slate-900">Multi-Tenancy & Data Isolation</h2>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed">
            Every query executed on Sellora is strictly scoped to your organization ID. Database row-level isolation
            guarantees that your marketplace financials, product unit costs, and customer orders are completely inaccessible
            to any other merchant.
          </p>

          <div className="flex items-center gap-2 text-xs text-emerald-700 font-medium">
            <Check className="h-4 w-4" />
            <span>Strict Tenant Isolation Active</span>
          </div>
        </div>
      </main>
    </div>
  );
}
