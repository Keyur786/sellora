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
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Import Data", href: "/import", icon: FileBarChart, badge: "New" },
  { name: "Products & COGS", href: "/products", icon: Package },
  { name: "Orders", href: "/orders", icon: ShoppingCart },
  { name: "Profit Breakdown", href: "/profit", icon: TrendingUp },
  { name: "Marketplaces", href: "/marketplaces", icon: Store, badge: "2 Active" },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-slate-200 bg-white shadow-sm">
      {/* Brand Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-slate-100 px-6">
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
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-emerald-50 text-emerald-700 font-semibold"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <div className="flex items-center gap-3">
                <item.icon
                  className={cn(
                    "h-5 w-5 transition-colors",
                    isActive ? "text-emerald-600" : "text-slate-400 group-hover:text-slate-600"
                  )}
                />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-medium text-emerald-800">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Store Indicator */}
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
    </aside>
  );
}
