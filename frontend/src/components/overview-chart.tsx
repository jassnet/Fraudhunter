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

const formatCompact = (value: number) =>
  value.toLocaleString("ja-JP", { notation: "compact", maximumFractionDigits: 1 });

type MetricKey = "clicks" | "conversions" | "suspicious_conversions";

const metricConfig: Array<{
  key: MetricKey;
  label: string;
  colorClass: string;
  barClass: string;
}> = [
  {
    key: "clicks",
    label: dashboardCopy.chart.legends.clicks,
    colorClass: "bg-foreground",
    barClass: "bg-foreground/95",
  },
  {
    key: "conversions",
    label: dashboardCopy.chart.legends.conversions,
    colorClass: "bg-[hsl(var(--info))]",
    barClass: "bg-[hsl(var(--info))]",
  },
  {
    key: "suspicious_conversions",
    label: dashboardCopy.chart.legends.suspiciousConversions,
    colorClass: "bg-destructive",
    barClass: "bg-destructive",
  },
];

export function OverviewChart({
  data,
  className,
  layout = "default",
}: {
  data: DailyStatsItem[];
  className?: string;
  layout?: "default" | "fill";
}) {
  if (!data || data.length === 0) {
    return (
      <div
        className={cn(
          "flex items-center justify-center text-sm text-muted-foreground",
          layout === "fill" ? "min-h-[10rem] flex-1" : "h-64",
          className
        )}
      >
        {dashboardCopy.chart.empty}
      </div>
    );
  }

  const rows = data.slice(-14);
  const maxByMetric = {
    clicks: Math.max(...rows.map((row) => safeNumber(row.clicks)), 1),
    conversions: Math.max(...rows.map((row) => safeNumber(row.conversions)), 1),
    suspicious_conversions: Math.max(...rows.map((row) => safeNumber(row.suspicious_conversions)), 1),
  };

  const chartLegend = (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-foreground/74">
      {metricConfig.map((metric) => (
        <span key={metric.key} className="inline-flex items-center gap-2">
          <span className={cn("h-2.5 w-2.5", metric.colorClass)} />
          {metric.label}
        </span>
      ))}
    </div>
  );

  const metricsRows = (
    <div className="min-h-0 flex-1 overflow-x-auto [scrollbar-gutter:stable]">
      <div className="min-w-[44rem] space-y-3">
        {metricConfig.map((metric, metricIndex) => {
          const metricMax = maxByMetric[metric.key];
          return (
            <section
              key={metric.key}
              className="grid grid-cols-[5.5rem_minmax(0,1fr)] items-stretch gap-3"
            >
              <div className="flex min-w-0 flex-col justify-between border-r border-border/70 pr-3 py-1">
                <div className="space-y-1">
                  <div className="inline-flex items-center gap-2 text-[12px] font-medium text-foreground/86">
                    <span className={cn("h-2.5 w-2.5 shrink-0", metric.colorClass)} />
                    <span className="truncate">{metric.label}</span>
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    最大 {metricMax.toLocaleString("ja-JP")}
                  </div>
                </div>
                <div className="text-[11px] text-foreground/60">{formatCompact(metricMax)}</div>
              </div>

              <div className="grid grid-cols-14 gap-2">
                {rows.map((row, index) => {
                  const value = safeNumber(row[metric.key]);
                  const barHeight = Math.max(6, Math.round((value / metricMax) * 100));
                  const tooltipLabel = [
                    row.date,
                    `${dashboardCopy.chart.legends.clicks} ${safeNumber(row.clicks).toLocaleString("ja-JP")}`,
                    `${dashboardCopy.chart.legends.conversions} ${safeNumber(row.conversions).toLocaleString("ja-JP")}`,
                    `${dashboardCopy.chart.legends.suspiciousConversions} ${safeNumber(
                      row.suspicious_conversions
                    ).toLocaleString("ja-JP")}`,
                  ].join("\n");
                  const showDateLabel = metricIndex === metricConfig.length - 1;
                  const showMobileLabel = index % 2 === 0;

                  return (
                    <div
                      key={`${metric.key}-${row.date}`}
                      title={tooltipLabel}
                      aria-label={tooltipLabel}
                      className="flex min-w-0 flex-col"
                    >
                      <div className="flex h-20 items-end border-b border-border/60 pb-1">
                        <div className="relative flex h-full w-full items-end">
                          <div className="absolute inset-x-0 top-[20%] border-t border-dashed border-border/35" />
                          <div className="absolute inset-x-0 top-[55%] border-t border-dashed border-border/35" />
                          <div
                            className={cn(
                              "relative w-full rounded-t-[2px] transition-[height,opacity] duration-200",
                              metric.barClass
                            )}
                            style={{ height: `${barHeight}%` }}
                          />
                        </div>
                      </div>
                      <div className="pt-1 text-center">
                        <div className="tabular-nums text-[11px] font-medium text-foreground/80">
                          {formatCompact(value)}
                        </div>
                        {showDateLabel ? (
                          <div
                            className={cn(
                              "mt-1 text-[10px] text-foreground/58",
                              !showMobileLabel && "hidden md:block"
                            )}
                          >
                            {formatDate(row.date)}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );

  if (layout === "fill") {
    return (
      <div className={cn("flex min-h-0 flex-1 flex-col gap-3", className)}>
        <div className="flex shrink-0 flex-wrap items-end justify-between gap-x-4 gap-y-2">
          <div className="space-y-1">
            <div className="text-[13px] font-medium text-foreground/86">{dashboardCopy.chart.title}</div>
            <div className="text-[11px] text-muted-foreground">
              選択日までの直近 {rows.length} 日を、指標ごとのスケールで表示しています。
            </div>
          </div>
          {chartLegend}
        </div>
        {metricsRows}
      </div>
    );
  }

  return (
    <div className={cn("space-y-5", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="text-[13px] font-medium text-foreground/86">{dashboardCopy.chart.title}</div>
          <div className="text-[11px] text-muted-foreground">
            選択日までの直近 {rows.length} 日を、指標ごとのスケールで表示しています。
          </div>
        </div>
        {chartLegend}
      </div>
      {metricsRows}
    </div>
  );
}
