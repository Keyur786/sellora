"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import { ListingGenerateResponse, Product } from "@/types";
import {
  Sparkles,
  Copy,
  Check,
  Package,
  Layers,
  ShieldCheck,
  Globe2,
  Tag,
  FileText,
  Store,
  RefreshCw,
} from "lucide-react";

export default function ListingStudioPage() {
  const [selectedMarketplace, setSelectedMarketplace] = useState<"amazon" | "flipkart">("amazon");
  const [selectedSku, setSelectedSku] = useState<string>("");
  const [title, setTitle] = useState("Pure Copper Hammered Water Bottle 1000ml");
  const [category, setCategory] = useState("Home & Kitchen");
  const [material, setMaterial] = useState("99.6% Pure Grade Certified Copper");
  const [features, setFeatures] = useState("Leak-proof silicone ring seal, Ayurvedic health benefits, artisanal hammered finish");
  const [targetAudience, setTargetAudience] = useState("Health-conscious individuals, office workers, yoga practitioners");
  const [price, setPrice] = useState("799");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Fetch catalog products to allow auto-fill
  const { data: products = [] } = useQuery({
    queryKey: ["products"],
    queryFn: () => api.getProducts(),
  });

  const [result, setResult] = useState<ListingGenerateResponse | null>(null);

  const generateMutation = useMutation({
    mutationFn: api.generateListing,
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleProductSelect = (sku: string) => {
    setSelectedSku(sku);
    const prod = products.find((p) => p.sku === sku);
    if (prod) {
      setTitle(prod.title);
      if (prod.category) setCategory(prod.category);
      if (prod.cost_price) setPrice(String(Number(prod.cost_price) * 2.5));
    }
  };

  const handleGenerate = (e: React.FormEvent) => {
    e.preventDefault();
    generateMutation.mutate({
      sku: selectedSku || undefined,
      title,
      category,
      marketplace: selectedMarketplace,
      material_or_specs: material,
      key_features: features,
      target_audience: targetAudience,
      selling_price: parseFloat(price) || undefined,
    });
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="flex-1 pb-16">
      <Header />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-7xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Listing Studio
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              SEO titles, bullet points, and search terms for Amazon and Flipkart.
            </p>
          </div>

          {/* Marketplace Channel Switcher */}
          <div className="flex items-center rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
            <button
              onClick={() => setSelectedMarketplace("amazon")}
              className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${
                selectedMarketplace === "amazon"
                  ? "bg-amber-500 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Store className="h-3.5 w-3.5" />
              <span>Amazon.in</span>
            </button>
            <button
              onClick={() => setSelectedMarketplace("flipkart")}
              className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${
                selectedMarketplace === "flipkart"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Store className="h-3.5 w-3.5" />
              <span>Flipkart</span>
            </button>
          </div>
        </div>

        {/* Studio Grid: Input Form (Left 1 col) and Output Preview (Right 2 cols) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Product Specs Form */}
          <div className="lg:col-span-5 rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Product Specifications</h2>
                <p className="text-[11px] text-slate-500">Pick from catalog or input custom attributes</p>
              </div>
              <Package className="h-4 w-4 text-slate-400" />
            </div>

            <form onSubmit={handleGenerate} className="space-y-4">
              {/* Quick SKU Pick */}
              {products.length > 0 && (
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Auto-fill from Catalog SKU</label>
                  <select
                    value={selectedSku}
                    onChange={(e) => handleProductSelect(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="">-- Choose Existing SKU --</option>
                    {products.map((p) => (
                      <option key={p.sku} value={p.sku}>
                        {p.sku} — {p.title.slice(0, 45)}...
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Product Title / Base Name */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Base Product Name *</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Copper Water Bottle"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  required
                />
              </div>

              {/* Category & Selling Price */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Category *</label>
                  <input
                    type="text"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    placeholder="e.g. Home & Kitchen"
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    required
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Selling Price (₹)</label>
                  <input
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    placeholder="799"
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>

              {/* Material & Build Specs */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Material & Technical Specs</label>
                <input
                  type="text"
                  value={material}
                  onChange={(e) => setMaterial(e.target.value)}
                  placeholder="e.g. 100% Pure Copper, 1000ml Capacity, 280 grams"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              {/* Key Features */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Key Features & Differentiators</label>
                <textarea
                  rows={2}
                  value={features}
                  onChange={(e) => setFeatures(e.target.value)}
                  placeholder="e.g. Leak proof lid, Ayurvedic benefits, gift packaging"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              {/* Target Audience */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Target Audience & Ideal Use Case</label>
                <input
                  type="text"
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                  placeholder="e.g. Daily office use, yoga enthusiasts, Diwali gift"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={generateMutation.isPending}
                className="w-full flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-xs font-semibold text-white shadow-md shadow-emerald-200 hover:bg-emerald-500 transition-all disabled:opacity-60"
              >
                {generateMutation.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Analyzing Keywords & Generating...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>Generate AI {selectedMarketplace.toUpperCase()} Listing</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Right Column: Output Assets Cards */}
          <div className="lg:col-span-7 space-y-6">
            {!result ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-12 text-center space-y-3">
                <Sparkles className="h-10 w-10 text-emerald-500 mx-auto animate-bounce" />
                <h3 className="text-sm font-bold text-slate-800">Your AI Listing Copy Will Appear Here</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  Click <strong>"Generate AI Listing"</strong> to produce SEO-optimized titles, 5 benefit-led bullets,
                  and high-converting Hinglish & vernacular search terms formatted for {selectedMarketplace.toUpperCase()} India.
                </p>
              </div>
            ) : (
              <div className="space-y-5 animate-in fade-in duration-200">
                {/* 1. Optimized Title */}
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-amber-100 text-amber-900 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
                        {result.marketplace.toUpperCase()} Optimized Title
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {result.optimized_title.length} / 200 chars
                      </span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(result.optimized_title, "title")}
                      className="flex items-center gap-1.5 rounded border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                    >
                      {copiedKey === "title" ? (
                        <Check className="h-3.5 w-3.5 text-emerald-600" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                      <span>{copiedKey === "title" ? "Copied!" : "Copy Title"}</span>
                    </button>
                  </div>
                  <p className="text-xs font-semibold text-slate-900 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100 font-mono">
                    {result.optimized_title}
                  </p>
                </div>

                {/* 2. Five Bullet Points */}
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Layers className="h-4 w-4 text-emerald-600" />
                      <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                        5 Conversion-Driven Bullet Points
                      </h3>
                    </div>
                    <button
                      onClick={() => copyToClipboard(result.bullet_points.join("\n\n"), "bullets")}
                      className="flex items-center gap-1.5 rounded border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                    >
                      {copiedKey === "bullets" ? (
                        <Check className="h-3.5 w-3.5 text-emerald-600" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                      <span>{copiedKey === "bullets" ? "Copied All" : "Copy Bullets"}</span>
                    </button>
                  </div>

                  <div className="space-y-2.5">
                    {result.bullet_points.map((bullet, idx) => (
                      <div key={idx} className="rounded-lg bg-slate-50 p-3 border border-slate-100 flex items-start justify-between gap-3 text-xs leading-relaxed text-slate-800">
                        <span>{bullet}</span>
                        <button
                          onClick={() => copyToClipboard(bullet, `b_${idx}`)}
                          className="shrink-0 p-1 text-slate-400 hover:text-slate-700"
                          title="Copy this bullet"
                        >
                          {copiedKey === `b_${idx}` ? (
                            <Check className="h-3.5 w-3.5 text-emerald-600" />
                          ) : (
                            <Copy className="h-3.5 w-3.5" />
                          )}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 3. Vernacular & Hinglish Search Queries */}
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Globe2 className="h-4 w-4 text-blue-600" />
                      <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                        Hinglish & Vernacular Search Terms (Indian Buyers)
                      </h3>
                    </div>
                    <button
                      onClick={() => copyToClipboard(result.vernacular_keywords.join(", "), "vernacular")}
                      className="flex items-center gap-1.5 rounded border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                    >
                      {copiedKey === "vernacular" ? (
                        <Check className="h-3.5 w-3.5 text-emerald-600" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                      <span>{copiedKey === "vernacular" ? "Copied" : "Copy Tags"}</span>
                    </button>
                  </div>

                  <div className="flex flex-wrap gap-2 pt-1">
                    {result.vernacular_keywords.map((kw, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center rounded-full bg-blue-50 border border-blue-200 px-3 py-1 text-xs font-medium text-blue-800"
                      >
                        <Tag className="h-3 w-3 mr-1 text-blue-500" />
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>

                {/* 4. Backend Search Terms & Description */}
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-purple-600" />
                      <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                        Amazon Backend Search Terms (Under 250 Bytes)
                      </h3>
                    </div>
                    <button
                      onClick={() => copyToClipboard(result.backend_search_terms.join(" "), "backend")}
                      className="flex items-center gap-1.5 rounded border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                    >
                      {copiedKey === "backend" ? (
                        <Check className="h-3.5 w-3.5 text-emerald-600" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                      <span>{copiedKey === "backend" ? "Copied" : "Copy Search Terms"}</span>
                    </button>
                  </div>

                  <p className="text-xs font-mono bg-purple-50/50 p-3 rounded-lg border border-purple-100 text-purple-900">
                    {result.backend_search_terms.join(" ")}
                  </p>

                  <div className="pt-2 border-t border-slate-100 flex items-center gap-2 text-xs text-slate-500">
                    <ShieldCheck className="h-4 w-4 text-emerald-600" />
                    <span>Guaranteed policy compliant: No punctuation, no duplicate words, no brand infringements.</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

