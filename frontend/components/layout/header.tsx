"use client";

import { Bell, ChevronDown, RefreshCw } from "lucide-react";

interface HeaderProps {
  days?: number;
  onDaysChange?: (days: number) => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function Header({ days = 30, onDaysChange, onRefresh, isRefreshing }: HeaderProps) {
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-8 backdrop-blur">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-slate-900">Seller Profitability Center</h1>
        <div className="flex items-center rounded-md bg-slate-100 p-1 text-xs font-medium text-slate-600">
          <button
            onClick={() => onDaysChange && onDaysChange(7)}
            className={`rounded px-2.5 py-1 transition-colors ${days === 7 ? "bg-white text-slate-900 shadow-sm" : "hover:text-slate-900"}`}
          >
            7D
          </button>
          <button
            onClick={() => onDaysChange && onDaysChange(14)}
            className={`rounded px-2.5 py-1 transition-colors ${days === 14 ? "bg-white text-slate-900 shadow-sm" : "hover:text-slate-900"}`}
          >
            14D
          </button>
          <button
            onClick={() => onDaysChange && onDaysChange(30)}
            className={`rounded px-2.5 py-1 transition-colors ${days === 30 ? "bg-white text-slate-900 shadow-sm" : "hover:text-slate-900"}`}
          >
            30D
          </button>
          <button
            onClick={() => onDaysChange && onDaysChange(90)}
            className={`rounded px-2.5 py-1 transition-colors ${days === 90 ? "bg-white text-slate-900 shadow-sm" : "hover:text-slate-900"}`}
          >
            90D
          </button>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin text-emerald-600" : ""}`} />
            <span>{isRefreshing ? "Syncing..." : "Sync Data"}</span>
          </button>
        )}

        {/* Marketplace status indicators */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
            <span>Amazon.in</span>
          </div>
          <div className="flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-800">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-500"></span>
            <span>Flipkart</span>
          </div>
        </div>

        {/* User avatar */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-slate-200">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-xs font-bold text-white">
            RS
          </div>
          <div className="hidden text-left sm:block">
            <p className="text-xs font-semibold text-slate-800">Rajesh Sharma</p>
            <p className="text-[10px] text-slate-500">seller@sellora.in</p>
          </div>
        </div>
      </div>
    </header>
  );
}
