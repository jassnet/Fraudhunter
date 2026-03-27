"use client";

import { Button } from "@/components/ui/button";
import { MetricBlock, MetricStrip } from "@/components/ui/metric-strip";
import { PageHeader } from "@/components/ui/page-header";
import { SectionFrame } from "@/components/ui/section-frame";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/ui/state-panel";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { OverviewChart } from "@/components/overview-chart";
import { dashboardCopy } from "@/copy/dashboard";
import { useDashboardData } from "@/hooks/use-dashboard-data";

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

const formatCoverage = (missingRate?: number | null) =>
  typeof missingRate === "number" ? `${Math.round((1 - missingRate) * 1000) / 10}%` : "-";

const formatRate = (value?: number | null) =>
  typeof value === "number" ? `${Math.round(value * 1000) / 10}%` : "-";

export default function DashboardPage() {
  const {
    summary,
    dailyStats,
    status,
    message,
    selectedDate,
    availableDates,
    lastUpdated,
    diagnostics,
    isRefreshing,
    handleDateChange,
    handleRefresh,
  } = useDashboardData();

  const actions = (
    <>
      <DateQuickSelect
        value={selectedDate}
        onChange={handleDateChange}
        availableDates={availableDates}
        showQuickButtons
      />
      <LastUpdated
        lastUpdated={lastUpdated}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
      />
    </>
  );

  const headerStatus =
    diagnostics.findingsStale && summary ? (
      <div className="text-[12px] text-[hsl(var(--warning))]">
        {dashboardCopy.states.staleTitle}
      </div>
    ) : null;

  if (status === "loading" || status === "refreshing") {
    return (
      <div className="flex h-full min-h-0 flex-col">
        <PageHeader
          title={dashboardCopy.title}
          meta={dashboardCopy.loadingMeta}
          actions={actions}
          status={headerStatus}
        />
        <div className="min-h-0 flex-1 overflow-auto">
          <div className="space-y-4 p-4 sm:p-6">
            <MetricStrip>
              {[...Array(4)].map((_, index) => (
                <div
                  key={index}
                  className="border-t border-border p-4 first:border-t-0 md:odd:border-r xl:border-t-0 xl:border-r xl:last:border-r-0"
                >
                  <Skeleton className="h-3 w-20" />
                  <Skeleton className="mt-5 h-12 w-28" />
                  <Skeleton className="mt-6 h-3 w-32" />
                </div>
              ))}
            </MetricStrip>
            <SectionFrame title={dashboardCopy.labels.diagnostics}>
              <Skeleton className="h-32 w-full" />
            </SectionFrame>
            <SectionFrame title={dashboardCopy.labels.chart}>
              <Skeleton className="h-64 w-full" />
            </SectionFrame>
          </div>
        </div>
      </div>
    );
  }

  if (
    status === "unauthorized" ||
    status === "forbidden" ||
    status === "transient-error" ||
    status === "error"
  ) {
    return (
      <div className="flex h-full min-h-0 flex-col">
        <PageHeader title={dashboardCopy.title} actions={actions} />
        <div className="min-h-0 flex-1 overflow-auto p-4 sm:p-6">
          <StatePanel
            title={
              status === "unauthorized"
                ? dashboardCopy.states.unauthorizedTitle
                : status === "forbidden"
                  ? dashboardCopy.states.forbiddenTitle
                  : status === "transient-error"
                    ? dashboardCopy.states.transientTitle
                    : "取得エラー"
            }
            message={message || dashboardCopy.states.loadError}
            tone={status === "forbidden" ? "danger" : status === "transient-error" ? "warning" : "neutral"}
            action={
              status === "transient-error" || status === "error" ? (
                <Button onClick={handleRefresh} variant="outline">
                  {dashboardCopy.states.retry}
                </Button>
              ) : undefined
            }
          />
        </div>
      </div>
    );
  }

  if (!summary || status === "empty") {
    return (
      <div className="flex h-full min-h-0 flex-col">
        <PageHeader title={dashboardCopy.title} actions={actions} />
        <div className="min-h-0 flex-1 overflow-auto p-4 sm:p-6">
          <StatePanel
            title={dashboardCopy.states.noDataTitle}
            message={dashboardCopy.states.noDataMessage}
            tone="neutral"
          />
        </div>
      </div>
    );
  }

  const clickDelta = formatDelta(summary.stats.clicks.total, summary.stats.clicks.prev_total);
  const conversionDelta = formatDelta(
    summary.stats.conversions.total,
    summary.stats.conversions.prev_total
  );

  return (
    <div className="flex h-full min-h-0 flex-col">
      <PageHeader
        title={dashboardCopy.title}
        meta={dashboardCopy.targetDateLabel(summary.date)}
        actions={actions}
        status={headerStatus}
      />

      <div className="min-h-0 flex-1 overflow-auto">
        <div className="space-y-4 p-4 sm:p-6">
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
              meta="一覧を開く"
              tone="warning"
              emphasis="alert"
              href="/suspicious/clicks"
              ariaLabel={`不審クリック ${summary.stats.suspicious.click_based}件を開く`}
            />
            <MetricBlock
              label={dashboardCopy.labels.suspiciousConversions}
              value={summary.stats.suspicious.conversion_based.toLocaleString()}
              meta="一覧を開く"
              tone="danger"
              emphasis="alert"
              href="/suspicious/conversions"
              ariaLabel={`不審コンバージョン ${summary.stats.suspicious.conversion_based}件を開く`}
            />
          </MetricStrip>

          <SectionFrame title={dashboardCopy.labels.diagnostics}>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <MetricBlock
                label={dashboardCopy.labels.coverage}
                value={formatCoverage(diagnostics.coverage?.missing_rate)}
                meta={
                  diagnostics.coverage
                    ? `${diagnostics.coverage.missing.toLocaleString()}件欠損`
                    : dashboardCopy.diagnosticsText.noSignal
                }
                emphasis="diagnostic"
              />
              <MetricBlock
                label={dashboardCopy.labels.enrichment}
                value={formatRate(diagnostics.enrichment?.success_rate)}
                meta={
                  diagnostics.enrichment
                    ? `${diagnostics.enrichment.enriched.toLocaleString()} / ${diagnostics.enrichment.total.toLocaleString()}`
                    : dashboardCopy.diagnosticsText.noSignal
                }
                emphasis="diagnostic"
              />
              <MetricBlock
                label={dashboardCopy.labels.findingsFreshness}
                value={diagnostics.findingsFreshness ? "最新" : "未計測"}
                meta={
                  diagnostics.findingsStale
                    ? dashboardCopy.diagnosticsText.stale
                    : dashboardCopy.diagnosticsText.healthy
                }
                tone={diagnostics.findingsStale ? "warning" : "neutral"}
                emphasis="diagnostic"
              />
              <MetricBlock
                label={dashboardCopy.labels.masterSync}
                value={diagnostics.masterSyncAt ? "同期済み" : "未同期"}
                meta={diagnostics.masterSyncAt || dashboardCopy.diagnosticsText.masterSyncMissing}
                emphasis="diagnostic"
              />
            </div>
          </SectionFrame>

          <SectionFrame title={dashboardCopy.labels.chart}>
            <OverviewChart data={dailyStats} />
          </SectionFrame>
        </div>
      </div>
    </div>
  );
}
