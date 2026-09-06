"use client";

import { RefreshCw, Menu } from "lucide-react";
import { useMobileNav } from "./mobile-nav";

interface HeaderProps {
  days?: number;
  onDaysChange?: (days: number) => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function Header({ days = 30, onDaysChange, onRefresh, isRefreshing }: HeaderProps) {
  const { open } = useMobileNav();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-4 sm:px-6 lg:px-8 backdrop-blur">
      {/* Left side: Hamburger button (mobile) & Title */}
      <div className="flex items-center gap-2.5 sm:gap-4 min-w-0">
        <button
          onClick={open}
          aria-label="Open navigation menu"
          className="flex lg:hidden items-center justify-center rounded-lg p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors shrink-0"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Mobile Brand Mark */}
        <div className="flex lg:hidden items-center gap-2 shrink-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-emerald-600 font-bold text-white text-xs shadow-sm">
            ₹
          </div>
          <span className="font-bold text-base tracking-tight text-slate-900 hidden xs:inline sm:hidden">Sellora</span>
        </div>

        <h1 className="text-base sm:text-lg font-semibold text-slate-900 truncate hidden md:block">
          Seller Profitability Center
        </h1>

        {/* Date Range Selector */}
        {onDaysChange && (
          <div className="flex items-center rounded-md bg-slate-100 p-0.5 sm:p-1 text-[11px] sm:text-xs font-medium text-slate-600 shrink-0">
            <button
              onClick={() => onDaysChange(7)}
              className={`rounded px-2 py-0.5 sm:px-2.5 sm:py-1 transition-colors ${
                days === 7 ? "bg-white text-slate-900 shadow-sm" : "hover:text-slate-900"
              }`}
            >
              7D
            </button>
            <button
              onClick={() => onDaysChange(14)}
              className={`rounded px-2 py-0.5 sm:px-2.5 sm:py-1 transition-colors ${
                days === 14 ? "bg-white text-slate-900 shadow-sm" : "hover:text-slate-900"
              }`}
            >
              14D
            </button>
            <button
              onClick={() => onDaysChange(30)}
              className={`rounded px-2 py-0.5 sm:px-2.5 sm:py-1 transition-colors ${
                days === 30 ? "bg-white text-slate-900 shadow-sm" : "hover:text-slate-900"
              }`}
            >
              30D
            </button>
            <button
              onClick={() => onDaysChange(90)}
              className={`rounded px-2 py-0.5 sm:px-2.5 sm:py-1 transition-colors ${
                days === 90 ? "bg-white text-slate-900 shadow-sm" : "hover:text-slate-900"
              }`}
            >
              90D
            </button>
          </div>
        )}
      </div>

      {/* Right side: Sync, Marketplace badges, and Avatar */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            aria-label="Sync Data"
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 sm:px-3 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 shrink-0 ${isRefreshing ? "animate-spin text-emerald-600" : ""}`} />
            <span className="hidden sm:inline">{isRefreshing ? "Syncing..." : "Sync Data"}</span>
          </button>
        )}

        {/* Marketplace status indicators (hidden on small phones to preserve space) */}
        <div className="hidden md:flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-0.5 text-[11px] font-medium text-amber-800">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
            <span>Amazon.in</span>
          </div>
          <div className="flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-2.5 py-0.5 text-[11px] font-medium text-blue-800">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-500"></span>
            <span>Flipkart</span>
          </div>
        </div>

        {/* User avatar */}
        <div className="flex items-center gap-2 pl-1.5 sm:pl-2 border-l border-slate-200">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-xs font-bold text-white shrink-0">
            RS
          </div>
          <div className="hidden xl:block text-left">
            <p className="text-xs font-semibold text-slate-800">Rajesh Sharma</p>
            <p className="text-[10px] text-slate-500">seller@sellora.in</p>
          </div>
        </div>
      </div>
    </header>
  );
}
