"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  TrendingUp,
  Receipt,
  Store,
  FileBarChart,
  Settings,
  Sparkles,
  RotateCcw,
  FileText,
  Megaphone,
  Tag,
  MessageSquareText,
  CalendarClock,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useMobileNav } from "./mobile-nav";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "AI Assistant", href: "/assistant", icon: MessageSquareText },
  { name: "Forecasting", href: "/forecasting", icon: CalendarClock },
  { name: "Pricing", href: "/pricing", icon: Tag },
  { name: "Listing Studio", href: "/listings", icon: Sparkles },
  { name: "Advertising", href: "/advertising", icon: Megaphone },
  { name: "Orders", href: "/orders", icon: ShoppingCart },
  { name: "Returns & RTO", href: "/returns", icon: RotateCcw },
  { name: "Expenses", href: "/expenses", icon: Receipt },
  { name: "Tax & GST", href: "/tax", icon: FileText },
  { name: "Profit Waterfall", href: "/profit", icon: TrendingUp },
  { name: "Products & COGS", href: "/products", icon: Package },
  { name: "Import Data", href: "/import", icon: FileBarChart },
  { name: "Marketplaces", href: "/marketplaces", icon: Store },
  { name: "Settings", href: "/settings", icon: Settings },
];

function NavItems({ onLinkClick }: { onLinkClick?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
      {navigation.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.name}
            href={item.href}
            onClick={onLinkClick}
            className={cn(
              "group flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-emerald-50 text-emerald-700 font-semibold"
                : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
            )}
          >
            <div className="flex items-center gap-3">
              <item.icon
                className={cn(
                  "h-5 w-5 transition-colors shrink-0",
                  isActive ? "text-emerald-600" : "text-slate-400 group-hover:text-slate-600"
                )}
              />
              <span className="truncate">{item.name}</span>
            </div>
          </Link>
        );
      })}
    </nav>
  );
}

function WorkspaceBadge() {
  return (
    <div className="border-t border-slate-100 p-4">
      <div className="rounded-lg bg-slate-50 p-3">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Workspace</p>
        <p className="mt-1 text-sm font-semibold text-slate-900 truncate">Apex Retail India</p>
        <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-500">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Amazon IN & Flipkart synced</span>
        </div>
      </div>
    </div>
  );
}

export function Sidebar() {
  const { isOpen, close } = useMobileNav();

  return (
    <>
      {/* 1. Desktop Static Sidebar (Visible on lg: and up) */}
      <aside className="hidden lg:flex fixed inset-y-0 left-0 z-30 w-64 flex-col border-r border-slate-200 bg-white shadow-sm">
        {/* Brand Logo */}
        <div className="flex h-16 items-center gap-3 border-b border-slate-100 px-6 shrink-0">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 font-bold text-white shadow-md shadow-emerald-200">
            ₹
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight text-slate-900">Sellora</span>
            <span className="ml-1.5 rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-700">
              India
            </span>
          </div>
        </div>

        {/* Navigation Menu */}
        <NavItems />

        {/* Bottom Store Indicator */}
        <WorkspaceBadge />
      </aside>

      {/* 2. Mobile Responsive Drawer (< lg screens) */}
      {isOpen && (
        <div className="lg:hidden">
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm transition-opacity"
            onClick={close}
            aria-hidden="true"
          />

          {/* Drawer Panel */}
          <aside className="fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col bg-white shadow-2xl animate-in slide-in-from-left duration-200">
            {/* Drawer Header */}
            <div className="flex h-16 items-center justify-between border-b border-slate-100 px-5 shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 font-bold text-white shadow-sm">
                  ₹
                </div>
                <div>
                  <span className="text-lg font-bold tracking-tight text-slate-900">Sellora</span>
                  <span className="ml-1.5 rounded bg-emerald-50 px-1 py-0.5 text-[9px] font-semibold text-emerald-700">
                    India
                  </span>
                </div>
              </div>
              <button
                onClick={close}
                aria-label="Close navigation menu"
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Navigation List */}
            <NavItems onLinkClick={close} />

            {/* Bottom Store Indicator */}
            <WorkspaceBadge />
          </aside>
        </div>
      )}
    </>
  );
}
