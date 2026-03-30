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
}

export function DashboardSummaryMetrics({
  summary,
}: DashboardSummaryMetricsProps) {
  const clickDelta = formatDelta(summary.stats.clicks.total, summary.stats.clicks.prev_total);
  const conversionDelta = formatDelta(
    summary.stats.conversions.total,
    summary.stats.conversions.prev_total
  );

  return (
    <MetricStrip>
      <MetricBlock
        label={dashboardCopy.labels.clicks}
        value={summary.stats.clicks.total.toLocaleString()}
        meta={`ユニークIP ${summary.stats.clicks.unique_ips.toLocaleString()}${clickDelta ? ` / ${clickDelta}` : ""}`}
        emphasis="primary"
      />
      <MetricBlock
        label={dashboardCopy.labels.conversions}
        value={summary.stats.conversions.total.toLocaleString()}
        meta={`ユニークIP ${summary.stats.conversions.unique_ips.toLocaleString()}${conversionDelta ? ` / ${conversionDelta}` : ""}`}
        emphasis="primary"
      />
      <MetricBlock
        label={dashboardCopy.labels.suspiciousClicks}
        value={summary.stats.suspicious.click_based.toLocaleString()}
        meta="一覧を表示"
        tone="warning"
        emphasis="alert"
        href="/suspicious/clicks"
        ariaLabel={`不審クリック ${summary.stats.suspicious.click_based} 件を表示`}
      />
      <MetricBlock
        label={dashboardCopy.labels.suspiciousConversions}
        value={summary.stats.suspicious.conversion_based.toLocaleString()}
        meta="一覧を表示"
        tone="danger"
        emphasis="alert"
        href="/suspicious/conversions"
        ariaLabel={`不審コンバージョン ${summary.stats.suspicious.conversion_based} 件を表示`}
      />
    </MetricStrip>
  );
}
