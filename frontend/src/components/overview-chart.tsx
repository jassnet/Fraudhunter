"use client";

import { DailyStatsItem } from "@/lib/api";
import { cn } from "@/lib/utils";

const safeNumber = (value?: number) => (Number.isFinite(value) ? value ?? 0 : 0);

const formatDate = (dateStr: string) => {
  const match = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return dateStr;
  return `${Number(match[2])}/${Number(match[3])}`;
};

export function OverviewChart({
  data,
  className,
}: {
  data: DailyStatsItem[];
  className?: string;
}) {
  if (!data || data.length === 0) {
    return (
      <div className={cn("flex h-64 items-center justify-center text-sm text-muted-foreground", className)}>
        表示できるデータがありません
      </div>
    );
  }

  const rows = data.slice(-14);
  const max = Math.max(
    ...rows.flatMap((row) => [safeNumber(row.clicks), safeNumber(row.conversions)]),
    1
  );

  return (
    <div className={cn("space-y-5", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-xs uppercase tracking-[0.14em] text-muted-foreground">クリック / CV</div>
        <div className="flex items-center gap-4 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
          <span className="inline-flex items-center gap-2">
            <span className="h-2.5 w-2.5 bg-foreground" />
            Click
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="h-2.5 w-2.5 bg-[hsl(var(--info))]" />
            CV
          </span>
        </div>
      </div>

      <div className="grid h-[clamp(11rem,28vh,16rem)] grid-cols-7 gap-3 md:grid-cols-14">
        {rows.map((row) => {
          const clicks = safeNumber(row.clicks);
          const conversions = safeNumber(row.conversions);
          return (
            <div key={row.date} className="flex min-w-0 flex-col justify-end gap-2">
              <div className="flex flex-1 items-end gap-1 border-l border-border pl-2">
                <div className="flex w-full items-end gap-1">
                  <div
                    className="w-1/2 bg-foreground"
                    style={{ height: `${Math.max(4, Math.round((clicks / max) * 100))}%` }}
                  />
                  <div
                    className="w-1/2 bg-[hsl(var(--info))]"
                    style={{ height: `${Math.max(4, Math.round((conversions / max) * 100))}%` }}
                  />
                </div>
              </div>
              <div className="space-y-1 text-[11px] text-muted-foreground">
                <div>{formatDate(row.date)}</div>
                <div className="tabular-nums text-[10px] uppercase tracking-[0.08em]">
                  {clicks}/{conversions}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
