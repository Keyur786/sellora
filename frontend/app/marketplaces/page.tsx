"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import {
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  ExternalLink,
  KeyRound,
  X,
  Radio,
  Zap,
  Check,
} from "lucide-react";
import { MarketplaceTestConnectionResponse } from "@/types";

export default function MarketplacesPage() {
  const queryClient = useQueryClient();

  // Dialog State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [sellerId, setSellerId] = useState("");
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [refreshToken, setRefreshToken] = useState("");
  const [testResult, setTestResult] = useState<MarketplaceTestConnectionResponse | null>(null);
  const [syncFeedback, setSyncFeedback] = useState<string | null>(null);

  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ["marketplaces"],
    queryFn: () => api.getMarketplaces(),
  });

  const amazonAccount = accounts.find((a) => a.marketplace_type === "amazon") || accounts[0];
  const flipkartAccount = accounts.find((a) => a.marketplace_type === "flipkart") || accounts[1];

  const syncMutation = useMutation({
    mutationFn: (id: string) => api.syncMarketplace(id),
    onSuccess: (data) => {
      setSyncFeedback(data.message);
      queryClient.invalidateQueries({ queryKey: ["marketplaces"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setTimeout(() => setSyncFeedback(null), 5000);
    },
    onError: (err: any) => {
      setSyncFeedback(`Sync failed: ${err.message || "Unknown error"}`);
    },
  });

  const testMutation = useMutation({
    mutationFn: (data: { seller_id?: string; client_id?: string; client_secret?: string; refresh_token?: string }) =>
      api.testAmazonConnection({
        marketplace_type: "amazon",
        seller_id: data.seller_id,
        client_id: data.client_id,
        client_secret: data.client_secret,
        refresh_token: data.refresh_token,
      }),
    onSuccess: (res) => {
      setTestResult(res);
    },
    onError: (err: any) => {
      setTestResult({
        success: false,
        connection_mode: "live",
        message: err.message || "Failed to reach server to test connection.",
        marketplace_name: "Amazon India",
        checked_at: new Date().toISOString(),
      });
    },
  });

  const saveCredentialsMutation = useMutation({
    mutationFn: (data: { seller_id?: string; client_id?: string; client_secret?: string; refresh_token?: string }) =>
      api.updateMarketplaceCredentials(amazonAccount?.id || "amazon", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["marketplaces"] });
      setIsModalOpen(false);
      setSyncFeedback("Amazon SP-API credentials saved successfully!");
      setTimeout(() => setSyncFeedback(null), 5000);
    },
  });

  const openConfigModal = () => {
    setSellerId(amazonAccount?.seller_id || "A2QWR8429184");
    setClientId("");
    setClientSecret("");
    setRefreshToken("");
    setTestResult(null);
    setIsModalOpen(true);
  };

  const isAmazonLive = amazonAccount?.connection_mode === "live";

  return (
    <div className="flex-1 pb-12">
      <Header />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-7xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Marketplaces</h1>
            <p className="text-xs text-slate-500 mt-1">
              Official Selling Partner API (SP-API) and channel integrations.
            </p>
          </div>
        </div>

        {syncFeedback && (
          <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3.5 flex items-center gap-2 text-xs text-emerald-800">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            <span>{syncFeedback}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Amazon India Card */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500 font-bold text-white shadow-sm text-lg">
                    a
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-base font-bold text-slate-900">Amazon India</h2>
                      {isAmazonLive ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                          <Zap className="h-3 w-3 fill-emerald-600" />
                          Live SP-API
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-700">
                          Developer Sandbox
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500">amazon.in (Marketplace ID: A21TJRUUN4KGV)</p>
                  </div>
                </div>

                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Connected</span>
                </span>
              </div>

              <div className="mt-6 space-y-2.5 rounded-lg bg-slate-50 p-4 text-xs">
                <div className="flex justify-between text-slate-600">
                  <span>Merchant / Seller ID:</span>
                  <span className="font-mono font-medium text-slate-900">
                    {amazonAccount?.seller_id || "A2QWR8429184"}
                  </span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>API Protocol:</span>
                  <span className="font-medium text-slate-900">Selling Partner API (v0 Orders/Finances)</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Regional Endpoint:</span>
                  <span className="font-mono text-slate-900">sellingpartnerapi-eu.amazon.com</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Authentication Standard:</span>
                  <span className="font-medium text-emerald-700 flex items-center gap-1">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Token-Only LWA (IAM-less)
                  </span>
                </div>
                <div className="flex justify-between text-slate-600 pt-1 border-t border-slate-200/60">
                  <span>Last Synchronized:</span>
                  <span className="font-medium text-slate-900">
                    {amazonAccount?.last_synced_at ? "Just now" : "Pending sync"}
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4 gap-2">
              <button
                onClick={openConfigModal}
                className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
              >
                <KeyRound className="h-3.5 w-3.5 text-slate-500" />
                <span>Configure SP-API Keys</span>
              </button>

              <button
                onClick={() => syncMutation.mutate(amazonAccount?.id || "amazon")}
                disabled={syncMutation.isPending}
                className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
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
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 font-bold text-white shadow-sm text-lg">
                    F
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">Flipkart Seller Hub</h2>
                    <p className="text-xs text-slate-500">seller.flipkart.com (FLIPKART_IN)</p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Connected</span>
                </span>
              </div>

              <div className="mt-6 space-y-2.5 rounded-lg bg-slate-50 p-4 text-xs">
                <div className="flex justify-between text-slate-600">
                  <span>Seller ID:</span>
                  <span className="font-mono font-medium text-slate-900">
                    {flipkartAccount?.seller_id || "FLIPKART_SELLER_881"}
                  </span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>API Protocol:</span>
                  <span className="font-medium text-slate-900">Flipkart Marketplace API</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Last Synchronized:</span>
                  <span className="font-medium text-slate-900">
                    {flipkartAccount?.last_synced_at ? "Just now" : "Pending sync"}
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4">
              <div className="flex items-center gap-1 text-[11px] text-slate-500">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                <span>OAuth Token Managed</span>
              </div>
              <button
                onClick={() => syncMutation.mutate(flipkartAccount?.id || "flipkart")}
                disabled={syncMutation.isPending}
                className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${syncMutation.isPending ? "animate-spin" : ""}`} />
                <span>Sync Now</span>
              </button>
            </div>
          </div>
        </div>

        {/* Modal: Amazon SP-API Credentials Configuration */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
            <div className="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-150">
              <div className="flex items-start justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500 text-white font-bold">
                    a
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">
                      Configure Amazon SP-API Credentials
                    </h2>
                    <p className="text-xs text-slate-500">
                      Live connection to Amazon India Seller Partner API
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 text-xs text-slate-600 space-y-1.5 leading-relaxed">
                <p className="font-semibold text-slate-900 flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  Token-Only Authentication (No AWS IAM / SigV4 needed)
                </p>
                <p>
                  To connect your real Amazon store, enter your Login with Amazon (LWA) app credentials
                  and seller refresh token. When saved, Sellora automatically fetches your live orders,
                  FBA inventory, and fee breakdowns.
                </p>
                <a
                  href="https://sellercentral.amazon.in/apps/manage"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-600 hover:underline pt-1"
                >
                  <span>Open Seller Central India App Management</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>

              {testResult && (
                <div
                  className={`rounded-lg p-3 text-xs border flex items-start gap-2 ${
                    testResult.success
                      ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                      : "bg-red-50 border-red-200 text-red-800"
                  }`}
                >
                  {testResult.success ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <p className="font-semibold">
                      {testResult.success ? "Connection Verified!" : "Connection Test Failed"}
                    </p>
                    <p className="text-[11px] mt-0.5">{testResult.message}</p>
                  </div>
                </div>
              )}

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  saveCredentialsMutation.mutate({
                    seller_id: sellerId,
                    client_id: clientId,
                    client_secret: clientSecret,
                    refresh_token: refreshToken,
                  });
                }}
                className="space-y-3.5 text-xs"
              >
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Seller / Merchant ID
                  </label>
                  <input
                    type="text"
                    required
                    value={sellerId}
                    onChange={(e) => setSellerId(e.target.value)}
                    placeholder="e.g. A2QWR8429184"
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    LWA Client ID (App ID)
                  </label>
                  <input
                    type="text"
                    value={clientId}
                    onChange={(e) => setClientId(e.target.value)}
                    placeholder="amzn1.application-oa2-client.xxxxxxxxxxxxxxxx"
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    LWA Client Secret
                  </label>
                  <input
                    type="password"
                    value={clientSecret}
                    onChange={(e) => setClientSecret(e.target.value)}
                    placeholder="amzn1.oa2-cs.v1.xxxxxxxxxxxxxxxx"
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    LWA Refresh Token
                  </label>
                  <textarea
                    rows={3}
                    value={refreshToken}
                    onChange={(e) => setRefreshToken(e.target.value)}
                    placeholder="Atzr|IwEBIA..."
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                  />
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    Leave blank to maintain developer sandbox mode, or enter your real token to activate live sync.
                  </p>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    disabled={testMutation.isPending}
                    onClick={() =>
                      testMutation.mutate({
                        seller_id: sellerId,
                        client_id: clientId,
                        client_secret: clientSecret,
                        refresh_token: refreshToken,
                      })
                    }
                    className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${testMutation.isPending ? "animate-spin" : ""}`} />
                    <span>Test Connection</span>
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setIsModalOpen(false)}
                      className="rounded-lg px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={saveCredentialsMutation.isPending}
                      className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-emerald-500 transition-colors disabled:opacity-50"
                    >
                      <Check className="h-3.5 w-3.5" />
                      <span>{saveCredentialsMutation.isPending ? "Saving..." : "Save Credentials"}</span>
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
