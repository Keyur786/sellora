"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { RefreshCw, CheckCircle2, AlertCircle, Plus, ShieldCheck, ExternalLink } from "lucide-react";

export default function MarketplacesPage() {
  const queryClient = useQueryClient();

  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ["marketplaces"],
    queryFn: () => api.getMarketplaces(),
  });

  const syncMutation = useMutation({
    mutationFn: (id: string) => api.syncMarketplace(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["marketplaces"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  return (
    <div className="flex-1 pb-12">
      <Header />

      <main className="px-8 py-6 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Connected Marketplaces</h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage your Amazon India and Flipkart integrations. Data is synchronized securely via official Selling Partner APIs.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Amazon India Card */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500 font-bold text-white shadow-sm">
                    a
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">Amazon India</h2>
                    <p className="text-xs text-slate-500">amazon.in (Marketplace: A21TJRUUN4KGV)</p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Connected</span>
                </span>
              </div>

              <div className="mt-6 space-y-3 rounded-lg bg-slate-50 p-4 text-xs">
                <div className="flex justify-between text-slate-600">
                  <span>Seller ID:</span>
                  <span className="font-mono font-medium text-slate-900">A2QWR8429184</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>API Protocol:</span>
                  <span className="font-medium text-slate-900">Selling Partner API (SP-API)</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Last Synchronized:</span>
                  <span className="font-medium text-slate-900">Just now</span>
                </div>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4">
              <div className="flex items-center gap-1 text-[11px] text-slate-500">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                <span>Encrypted OAuth token</span>
              </div>
              <button
                onClick={() => syncMutation.mutate("amazon")}
                disabled={syncMutation.isPending}
                className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800 transition-colors"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${syncMutation.isPending ? "animate-spin" : ""}`} />
                <span>Sync Now</span>
              </button>
            </div>
          </div>

          {/* Flipkart Card */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 font-bold text-white shadow-sm">
                    F
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">Flipkart Seller Hub</h2>
                    <p className="text-xs text-slate-500">seller.flipkart.com</p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Connected</span>
                </span>
              </div>

              <div className="mt-6 space-y-3 rounded-lg bg-slate-50 p-4 text-xs">
                <div className="flex justify-between text-slate-600">
                  <span>Seller ID:</span>
                  <span className="font-mono font-medium text-slate-900">FLIPKART_SELLER_881</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>API Protocol:</span>
                  <span className="font-medium text-slate-900">Flipkart Marketplace API</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Last Synchronized:</span>
                  <span className="font-medium text-slate-900">Just now</span>
                </div>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4">
              <div className="flex items-center gap-1 text-[11px] text-slate-500">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                <span>Encrypted OAuth token</span>
              </div>
              <button
                onClick={() => syncMutation.mutate("flipkart")}
                disabled={syncMutation.isPending}
                className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800 transition-colors"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${syncMutation.isPending ? "animate-spin" : ""}`} />
                <span>Sync Now</span>
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
