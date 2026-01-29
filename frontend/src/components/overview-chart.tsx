"use client";

import { DailyStatsItem } from "@/lib/api";
import { cn } from "@/lib/utils";

const safeNumber = (value?: number) => (Number.isFinite(value) ? value ?? 0 : 0);

export function OverviewChart({
  data,
  className,
}: {
  data: DailyStatsItem[];
  className?: string;
}) {
  if (!data || data.length === 0) {
    return (
      <div className={cn("flex h-[280px] items-center justify-center text-sm text-muted-foreground", className)}>
        No data
      </div>
    );
  }

  const max = Math.max(
    ...data.map((d) => Math.max(safeNumber(d.clicks), safeNumber(d.conversions), 1))
  );

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-blue-500" />
          Clicks
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          Conversions
        </span>
      </div>
      {data.slice(-30).map((row) => {
        const clickVal = safeNumber(row.clicks);
        const convVal = safeNumber(row.conversions);
        const clickPct = Math.round((clickVal / max) * 100);
        const convPct = Math.round((convVal / max) * 100);
        return (
          <div key={row.date} className="space-y-1">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{row.date}</span>
              <span>
                Clicks {clickVal.toLocaleString()} | Conversions {convVal.toLocaleString()}
              </span>
            </div>
            <div className="space-y-1">
              <div className="h-2 rounded bg-muted">
                <div className="h-2 rounded bg-blue-500" style={{ width: `${clickPct}%` }} />
              </div>
              <div className="h-2 rounded bg-muted">
                <div className="h-2 rounded bg-emerald-500" style={{ width: `${convPct}%` }} />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
