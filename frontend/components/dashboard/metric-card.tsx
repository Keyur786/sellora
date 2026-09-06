import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string;
  subtext?: string;
  change?: string;
  isPositive?: boolean;
  icon: LucideIcon;
  variant?: "default" | "success" | "warning" | "danger";
}

export function MetricCard({
  title,
  value,
  subtext,
  change,
  isPositive,
  icon: Icon,
  variant = "default",
}: MetricCardProps) {
  const variantStyles = {
    default: "bg-white border-slate-200 text-slate-900",
    success: "bg-emerald-50/60 border-emerald-200 text-emerald-950",
    warning: "bg-amber-50/60 border-amber-200 text-amber-950",
    danger: "bg-rose-50/60 border-rose-200 text-rose-950",
  };

  const iconStyles = {
    default: "bg-slate-100 text-slate-700",
    success: "bg-emerald-100 text-emerald-700",
    warning: "bg-amber-100 text-amber-700",
    danger: "bg-rose-100 text-rose-700",
  };

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border p-5 shadow-sm transition-all hover:shadow-md",
        variantStyles[variant]
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</span>
        <div className={cn("flex h-9 w-9 items-center justify-center rounded-lg", iconStyles[variant])}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <div className="mt-3">
        <div className="text-2xl font-bold tracking-tight text-slate-900">{value}</div>
        <div className="mt-1 flex items-center gap-2">
          {change && (
            <span
              className={cn(
                "text-xs font-semibold",
                isPositive ? "text-emerald-600" : "text-rose-600"
              )}
            >
              {change}
            </span>
          )}
          {subtext && <span className="text-xs text-slate-500">{subtext}</span>}
        </div>
      </div>
    </div>
  );
}
