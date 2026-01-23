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
    <div className={cn("space-y-3", className)}>
      {data.slice(-14).map((row) => {
        const clickVal = safeNumber(row.clicks);
        const convVal = safeNumber(row.conversions);
        const clickPct = Math.round((clickVal / max) * 100);
        const convPct = Math.round((convVal / max) * 100);
        return (
          <div key={row.date} className="space-y-1">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{row.date}</span>
              <span>
                Clicks {clickVal.toLocaleString()} ? Conversions {convVal.toLocaleString()}
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
