"use client";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { MetricBlock, MetricStrip } from "@/components/ui/metric-strip";
import { PageHeader } from "@/components/ui/page-header";
import { SectionFrame } from "@/components/ui/section-frame";
import { Skeleton } from "@/components/ui/skeleton";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { OverviewChart } from "@/components/overview-chart";
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

export default function DashboardPage() {
  const {
    summary,
    dailyStats,
    loading,
    error,
    selectedDate,
    availableDates,
    lastUpdated,
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

  if (loading) {
    return (
      <div className="flex h-full min-h-0 flex-col">
        <PageHeader title="ダッシュボード" meta="読込中" actions={actions} />
        <div className="min-h-0 flex-1 overflow-auto">
          <div className="space-y-4 p-4 sm:p-6">
          <MetricStrip>
            {[...Array(4)].map((_, index) => (
              <div key={index} className="border-t border-border p-4 first:border-t-0 md:odd:border-r xl:border-t-0 xl:border-r xl:last:border-r-0">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="mt-5 h-12 w-28" />
                <Skeleton className="mt-6 h-3 w-32" />
              </div>
            ))}
          </MetricStrip>
          <SectionFrame title="30日推移">
            <Skeleton className="h-64 w-full" />
          </SectionFrame>
        </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full min-h-0 flex-col">
        <PageHeader title="ダッシュボード" actions={actions} />
        <div className="min-h-0 flex-1 overflow-auto p-4 sm:p-6">
          <EmptyState
            title="取得エラー"
            message={error}
            action={
              <Button onClick={handleRefresh} variant="outline">
                再試行
              </Button>
            }
          />
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="flex h-full min-h-0 flex-col">
        <PageHeader title="ダッシュボード" actions={actions} />
        <div className="min-h-0 flex-1 overflow-auto p-4 sm:p-6">
          <EmptyState
            title="データなし"
            message="表示対象の集計がありません。"
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
      <PageHeader title="ダッシュボード" meta={`対象日 ${summary.date}`} actions={actions} />

      <div className="min-h-0 flex-1 overflow-auto">
        <div className="space-y-4 p-4 sm:p-6">
        <MetricStrip>
          <MetricBlock
            label="クリック"
            value={summary.stats.clicks.total.toLocaleString()}
            meta={`ユニークIP ${summary.stats.clicks.unique_ips.toLocaleString()}${clickDelta ? ` / ${clickDelta}` : ""}`}
          />
          <MetricBlock
            label="CV"
            value={summary.stats.conversions.total.toLocaleString()}
            meta={`ユニークIP ${summary.stats.conversions.unique_ips.toLocaleString()}${conversionDelta ? ` / ${conversionDelta}` : ""}`}
          />
          <MetricBlock
            label="不審クリック"
            value={summary.stats.suspicious.click_based.toLocaleString()}
            meta="一覧を開く"
            tone="warning"
            href="/suspicious/clicks"
            ariaLabel={`不審クリック ${summary.stats.suspicious.click_based}件を開く`}
          />
          <MetricBlock
            label="不審CV"
            value={summary.stats.suspicious.conversion_based.toLocaleString()}
            meta="一覧を開く"
            tone="danger"
            href="/suspicious/conversions"
            ariaLabel={`不審コンバージョン ${summary.stats.suspicious.conversion_based}件を開く`}
          />
        </MetricStrip>

        <SectionFrame title="30日推移">
          <OverviewChart data={dailyStats} />
        </SectionFrame>
      </div>
      </div>
    </div>
  );
}
