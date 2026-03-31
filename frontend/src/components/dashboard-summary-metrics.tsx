import { MetricBlock, MetricStrip } from "@/components/ui/metric-strip";
import { dashboardCopy } from "@/copy/dashboard";
import type { SummaryResponse } from "@/lib/api";

const formatDelta = (current: number, previous?: number | null) => {
  if (previous === undefined || previous === null) return null;
  const delta = current - previous;
  const sign = delta > 0 ? "+" : "";
  const deltaLabel = `${sign}${delta.toLocaleString()}`;
  if (previous <= 0) return `前日比 ${deltaLabel}`;
  const pct = Math.round((delta / previous) * 1000) / 10;
  const pctSign = pct > 0 ? "+" : "";
  return `前日比 ${deltaLabel} (${pctSign}${pct}%)`;
};

interface DashboardSummaryMetricsProps {
  summary: SummaryResponse;
  compact?: boolean;
}

export function DashboardSummaryMetrics({
  summary,
  compact = false,
}: DashboardSummaryMetricsProps) {
  const clickDelta = formatDelta(summary.stats.clicks.total, summary.stats.clicks.prev_total);
  const conversionDelta = formatDelta(
    summary.stats.conversions.total,
    summary.stats.conversions.prev_total
  );

  return (
    <MetricStrip columns={3}>
      <MetricBlock
        label={dashboardCopy.labels.clicks}
        value={summary.stats.clicks.total.toLocaleString()}
        meta={`ユニークIP ${summary.stats.clicks.unique_ips.toLocaleString()}${clickDelta ? ` / ${clickDelta}` : ""}`}
        emphasis="primary"
        compact={compact}
      />
      <MetricBlock
        label={dashboardCopy.labels.conversions}
        value={summary.stats.conversions.total.toLocaleString()}
        meta={`ユニークIP ${summary.stats.conversions.unique_ips.toLocaleString()}${conversionDelta ? ` / ${conversionDelta}` : ""}`}
        emphasis="primary"
        compact={compact}
      />
      <MetricBlock
        label={dashboardCopy.labels.suspiciousConversions}
        value={summary.stats.suspicious.conversion_based.toLocaleString()}
        meta={
          <span className="inline-flex items-center gap-1 font-medium text-foreground">
            一覧を見る
            <span aria-hidden>→</span>
          </span>
        }
        tone="danger"
        emphasis="alert"
        href="/suspicious/conversions"
        ariaLabel={`不審コンバージョン ${summary.stats.suspicious.conversion_based} 件の一覧を見る`}
        compact={compact}
      />
    </MetricStrip>
  );
}
