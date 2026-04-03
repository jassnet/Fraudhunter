import type { ReactNode } from "react";
import Link from "next/link";
import { dashboardCopy } from "@/features/dashboard/copy";
import type { SummaryResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

const formatDelta = (current: number, previous?: number | null) => {
  if (previous === undefined || previous === null) return null;
  const delta = current - previous;
  const sign = delta > 0 ? "+" : "";
  const deltaLabel = `${sign}${delta.toLocaleString("ja-JP")}`;
  if (previous <= 0) return `前日比 ${deltaLabel}`;
  const pct = Math.round((delta / previous) * 1000) / 10;
  const pctSign = pct > 0 ? "+" : "";
  return `前日比 ${deltaLabel} / ${pctSign}${pct}%`;
};

interface DashboardSummaryMetricsProps {
  summary: SummaryResponse;
  compact?: boolean;
}

function SummaryMetric({
  label,
  value,
  meta,
  tone = "neutral",
  href,
  ariaLabel,
  compact = false,
}: {
  label: string;
  value: string;
  meta: ReactNode;
  tone?: "neutral" | "danger";
  href?: string;
  ariaLabel?: string;
  compact?: boolean;
}) {
  const content = (
    <div
      className={cn(
        "relative flex flex-col justify-between border-t border-border first:border-t-0 md:first:border-t md:odd:border-r xl:border-t-0 xl:border-r xl:last:border-r-0",
        compact ? "min-h-[100px] p-3 xl:min-h-[108px]" : "min-h-[152px] p-4"
      )}
    >
      <div className="space-y-2">
        <div
          className={cn(
            "text-[12px] font-semibold tracking-[0.02em]",
            tone === "danger" ? "text-destructive" : "text-foreground/82"
          )}
        >
          {label}
        </div>
        <div
          className={cn(
            "font-bold tracking-[-0.04em] tabular-nums",
            compact ? "text-[2rem]" : "text-[2.65rem]",
            tone === "danger" ? "text-destructive" : "text-foreground"
          )}
        >
          {value}
        </div>
      </div>
      <div
        className={cn(
          compact ? "text-[12px] leading-snug" : "text-[13px] leading-5",
          tone === "danger" ? "text-foreground/86" : "text-foreground/80"
        )}
      >
        {meta}
      </div>
    </div>
  );

  if (!href) return content;
  return (
    <Link
      href={href}
      aria-label={ariaLabel ?? label}
      className="transition-colors hover:bg-white/[0.07] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white"
    >
      {content}
    </Link>
  );
}

export function DashboardSummaryMetrics({
  summary,
  compact = false,
}: DashboardSummaryMetricsProps) {
  const fraudFindings = Number(summary.stats.suspicious.fraud_findings ?? 0);
  const fraudFindingsLabel = fraudFindings.toLocaleString("ja-JP");
  const clickDelta = formatDelta(summary.stats.clicks.total, summary.stats.clicks.prev_total);
  const conversionDelta = formatDelta(
    summary.stats.conversions.total,
    summary.stats.conversions.prev_total
  );
  const fraudHref = summary.date
    ? `/suspicious/fraud?date=${encodeURIComponent(summary.date)}`
    : "/suspicious/fraud";

  return (
    <section className="grid border border-border bg-card md:grid-cols-2 xl:grid-cols-3">
      <SummaryMetric
        label={dashboardCopy.labels.clicks}
        value={summary.stats.clicks.total.toLocaleString("ja-JP")}
        meta={`ユニークIP ${summary.stats.clicks.unique_ips.toLocaleString("ja-JP")}${clickDelta ? ` / ${clickDelta}` : ""}`}
        compact={compact}
      />
      <SummaryMetric
        label={dashboardCopy.labels.conversions}
        value={summary.stats.conversions.total.toLocaleString("ja-JP")}
        meta={`ユニークIP ${summary.stats.conversions.unique_ips.toLocaleString("ja-JP")}${conversionDelta ? ` / ${conversionDelta}` : ""}`}
        compact={compact}
      />
      <SummaryMetric
        label={dashboardCopy.labels.suspiciousConversions}
        value={fraudFindingsLabel}
        meta={
          <span className="inline-flex items-center gap-1 font-medium text-foreground">
            不正判定一覧
            <span aria-hidden>/</span>
            <span>詳細へ</span>
          </span>
        }
        tone="danger"
        href={fraudHref}
        ariaLabel={`不正判定 ${fraudFindingsLabel}件の一覧を表示`}
        compact={compact}
      />
    </section>
  );
}
