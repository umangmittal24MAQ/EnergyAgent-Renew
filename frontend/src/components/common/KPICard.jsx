import React from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

export const KPICard = ({
  title,
  value,
  displayValue = null,
  unit = "",
  subtitle = "",
  delta = null,
  deltaLabel = "",
  icon: Icon = null,
  color = "blue",
}) => {
  const colorClasses = {
    blue: "text-[#1d4f91]",
    green: "text-[#1f7a5a]",
    yellow: "text-[#8a6a2f]",
    red: "text-[#b4233d]",
  };

  const iconBgClasses = {
    blue: "bg-blue-50 text-blue-500",
    green: "bg-emerald-50 text-emerald-500",
    yellow: "bg-amber-50 text-amber-500",
    red: "bg-rose-50 text-rose-500",
  };

  const isDeltaPositive = delta !== null && delta >= 0;
  const formattedValue =
    displayValue !== null && displayValue !== undefined
      ? String(displayValue)
      : typeof value === "number"
        ? value.toLocaleString("en-IN", {
            maximumFractionDigits: 1,
          })
        : value || "—";

  return (
    <div className="h-full overflow-hidden rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow duration-200 hover:shadow-md">
      <div className="mb-3 flex items-start justify-between gap-3">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          {title}
        </p>

        <div
          className={`${iconBgClasses[color] || iconBgClasses.blue} flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${Icon ? "opacity-100" : "opacity-0"}`}
          aria-hidden={!Icon}
        >
          {Icon ? (
            <Icon size={18} strokeWidth={1.9} />
          ) : (
            <span className="block h-4 w-4" />
          )}
        </div>
      </div>

      <div className="mt-2 flex items-end gap-2">
        <p
          className={`wrap-break-word text-3xl font-bold leading-none tracking-tight ${colorClasses[color] || colorClasses.blue}`}
        >
          {formattedValue}
        </p>
        {unit && (
          <p className="whitespace-nowrap pb-1 text-base font-normal text-slate-400">
            {unit}
          </p>
        )}
      </div>

      {subtitle && (
        <p className="mt-1 text-xs font-normal text-slate-400">{subtitle}</p>
      )}

      {delta !== null && (
        <div className="mt-4 flex items-center gap-2 border-t border-(--surface-border) pt-3">
          {isDeltaPositive ? (
            <>
              <TrendingUp size={16} className="text-(--success-600)" />
              <span className="text-(--success-600) text-sm font-medium">
                +{delta.toFixed(2)} {deltaLabel}
              </span>
            </>
          ) : (
            <>
              <TrendingDown size={16} className="text-(--danger-600)" />
              <span className="text-(--danger-600) text-sm font-medium">
                {delta.toFixed(2)} {deltaLabel}
              </span>
            </>
          )}
        </div>
      )}
    </div>
  );
};
