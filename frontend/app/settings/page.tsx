"use client";

import { Header } from "@/components/layout/header";
import { Building2, Key, Bell, Shield, Check } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="flex-1 pb-12">
      <Header />

      <main className="px-8 py-6 space-y-6 max-w-4xl">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Organization Settings</h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage your store details, marketplace credentials, and tenant configuration.
          </p>
        </div>

        {/* Store Details Card */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Building2 className="h-5 w-5 text-emerald-600" />
            <h2 className="text-base font-semibold text-slate-900">Store Profile</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="font-medium text-slate-700 block mb-1">Organization Name</label>
              <input
                type="text"
                disabled
                value="Apex Retail India"
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-slate-700"
              />
            </div>
            <div>
              <label className="font-medium text-slate-700 block mb-1">Organization Slug (Tenant ID)</label>
              <input
                type="text"
                disabled
                value="demo-seller-india"
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-slate-700"
              />
            </div>
            <div>
              <label className="font-medium text-slate-700 block mb-1">Base Currency</label>
              <input
                type="text"
                disabled
                value="INR (₹) - Indian Rupee"
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-slate-700"
              />
            </div>
            <div>
              <label className="font-medium text-slate-700 block mb-1">Timezone</label>
              <input
                type="text"
                disabled
                value="Asia/Kolkata (IST)"
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-slate-700"
              />
            </div>
          </div>
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
