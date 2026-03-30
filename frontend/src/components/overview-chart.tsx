"use client";

import { dashboardCopy } from "@/copy/dashboard";
import type { DailyStatsItem } from "@/lib/api";
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
      <div
        className={cn(
          "flex h-64 items-center justify-center text-sm text-muted-foreground",
          className
        )}
      >
        {dashboardCopy.chart.empty}
      </div>
    );
  }

  const rows = data.slice(-14);
  const max = Math.max(
    ...rows.flatMap((row) => [
      safeNumber(row.clicks),
      safeNumber(row.conversions),
      safeNumber(row.suspicious_clicks),
      safeNumber(row.suspicious_conversions),
    ]),
    1
  );

  return (
    <div className={cn("space-y-5", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-[13px] font-medium text-foreground/86">
          {dashboardCopy.chart.title}
        </div>
        <div className="flex flex-wrap items-center gap-4 text-[12px] text-foreground/74">
          <span className="inline-flex items-center gap-2">
            <span className="h-2.5 w-2.5 bg-foreground" />
            {dashboardCopy.chart.legends.clicks}
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="h-2.5 w-2.5 bg-[hsl(var(--info))]" />
            {dashboardCopy.chart.legends.conversions}
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="h-2.5 w-2.5 bg-[hsl(var(--warning))]" />
            {dashboardCopy.chart.legends.suspiciousClicks}
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="h-2.5 w-2.5 bg-destructive" />
            {dashboardCopy.chart.legends.suspiciousConversions}
          </span>
        </div>
      </div>

      <div className="grid h-[clamp(13rem,30vh,18rem)] grid-cols-7 gap-3 md:grid-cols-14">
        {rows.map((row) => {
          const clicks = safeNumber(row.clicks);
          const conversions = safeNumber(row.conversions);
          const suspiciousClicks = safeNumber(row.suspicious_clicks);
          const suspiciousConversions = safeNumber(row.suspicious_conversions);

          return (
            <div key={row.date} className="flex min-w-0 flex-col justify-end gap-2">
              <div className="flex flex-1 items-end gap-1 border-l border-border pl-2">
                <div className="flex w-full items-end gap-1">
                  <div
                    className="w-1/4 bg-foreground/95"
                    style={{ height: `${Math.max(4, Math.round((clicks / max) * 100))}%` }}
                  />
                  <div
                    className="w-1/4 bg-[hsl(var(--info))]"
                    style={{ height: `${Math.max(4, Math.round((conversions / max) * 100))}%` }}
                  />
                  <div
                    className="w-1/4 bg-[hsl(var(--warning))]"
                    style={{
                      height: `${Math.max(4, Math.round((suspiciousClicks / max) * 100))}%`,
                    }}
                  />
                  <div
                    className="w-1/4 bg-destructive"
                    style={{
                      height: `${Math.max(
                        4,
                        Math.round((suspiciousConversions / max) * 100)
                      )}%`,
                    }}
                  />
                </div>
              </div>
              <div className="space-y-1 text-[12px] text-foreground/82">
                <div>{formatDate(row.date)}</div>
                <div className="tabular-nums text-[11px] text-foreground/66">
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
