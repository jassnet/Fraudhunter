"use client";

import Link from "next/link";
import { OverviewChart } from "@/components/overview-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { useDashboardData } from "@/hooks/use-dashboard-data";

const formatDelta = (current: number, previous?: number | null) => {
  if (previous === undefined || previous === null) return null;
  const delta = current - previous;
  const sign = delta > 0 ? "+" : "";
  const deltaLabel = `${sign}${delta.toLocaleString()}`;
  if (previous <= 0) return deltaLabel;
  const pct = Math.round((delta / previous) * 1000) / 10;
  const pctSign = pct > 0 ? "+" : "";
  return `${deltaLabel}（${pctSign}${pct}%）`;
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

  if (loading) {
    return (
      <div className="flex-1 space-y-5 p-6 sm:p-8">
        <Skeleton className="h-12 rounded" />
        <div className="grid grid-cols-2 xl:grid-cols-4 divide-x divide-y divide-slate-200 border border-slate-200">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-[130px] rounded-none" />
          ))}
        </div>
        <Skeleton className="h-[460px] rounded" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 p-6 sm:p-8">
        <Card className="border-destructive/30 bg-white">
          <CardHeader>
            <CardTitle className="text-destructive">取得エラー</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{error}</p>
            <Button onClick={handleRefresh}>再試行</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="p-6 sm:p-8">
        <Card className="border-slate-200 bg-white">
          <CardHeader>
            <CardTitle>表示できるデータがありません</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            別の日付を選択するか、データ取込が完了しているか確認してください。
          </CardContent>
        </Card>
      </div>
    );
  }

  const clickDelta = formatDelta(summary.stats.clicks.total, summary.stats.clicks.prev_total);
  const conversionDelta = formatDelta(
    summary.stats.conversions.total,
    summary.stats.conversions.prev_total
  );

  return (
    <div className="flex-1">
      <header className="flex flex-wrap items-center gap-x-6 gap-y-3 border-b border-slate-200 px-6 py-5 sm:px-8">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-950">ダッシュボード</h1>
        <span className="text-sm text-slate-500">基準日: {summary.date}</span>
        <div className="ml-auto flex flex-wrap items-center gap-3">
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
        </div>
      </header>

      <div className="p-6 sm:p-8">
        <section className="grid grid-cols-2 xl:grid-cols-4 divide-x divide-y divide-slate-200 border border-slate-200 bg-white">
          <div>
            <div className="h-1.5 bg-slate-700" />
            <div className="p-5">
              <div className="text-xs font-semibold tracking-[0.08em] text-slate-500">総クリック数</div>
              <div className="mt-3 text-[2.4rem] font-semibold tracking-[-0.04em] text-slate-900 tabular-nums">
                {summary.stats.clicks.total.toLocaleString()}
              </div>
              <div className="mt-3 text-sm leading-6 text-slate-500">
                ユニーク IP {summary.stats.clicks.unique_ips.toLocaleString()}
                {clickDelta ? ` / 前日比 ${clickDelta}` : ""}
              </div>
            </div>
          </div>
          <div>
            <div className="h-1.5 bg-teal-600" />
            <div className="p-5">
              <div className="text-xs font-semibold tracking-[0.08em] text-slate-500">総コンバージョン数</div>
              <div className="mt-3 text-[2.4rem] font-semibold tracking-[-0.04em] text-slate-900 tabular-nums">
                {summary.stats.conversions.total.toLocaleString()}
              </div>
              <div className="mt-3 text-sm leading-6 text-slate-500">
                ユニーク IP {summary.stats.conversions.unique_ips.toLocaleString()}
                {conversionDelta ? ` / 前日比 ${conversionDelta}` : ""}
              </div>
            </div>
          </div>
          <Link
            href="/suspicious/clicks"
            className="block"
            aria-label={`不審クリック ${summary.stats.suspicious.click_based}件の一覧を確認`}
          >
            <div className="h-1.5 bg-amber-400" />
            <div className="p-5">
              <div className="text-xs font-semibold tracking-[0.08em] text-amber-700">不審クリック</div>
              <div className="mt-3 text-[2.4rem] font-semibold tracking-[-0.04em] text-amber-700 tabular-nums">
                {summary.stats.suspicious.click_based}
              </div>
              <div className="mt-3 text-sm leading-6 text-amber-800">閾値超過のクリックを一覧で確認</div>
              <div className="mt-1 text-xs font-medium tracking-[0.04em] text-amber-700">一覧で詳細を確認 →</div>
            </div>
          </Link>
          <Link
            href="/suspicious/conversions"
            className="block"
            aria-label={`不審コンバージョン ${summary.stats.suspicious.conversion_based}件の一覧を確認`}
          >
            <div className="h-1.5 bg-rose-400" />
            <div className="p-5">
              <div className="text-xs font-semibold tracking-[0.08em] text-rose-700">不審コンバージョン</div>
              <div className="mt-3 text-[2.4rem] font-semibold tracking-[-0.04em] text-rose-700 tabular-nums">
                {summary.stats.suspicious.conversion_based}
              </div>
              <div className="mt-3 text-sm leading-6 text-rose-800">CV 起点の不審な流入を一覧で確認</div>
              <div className="mt-1 text-xs font-medium tracking-[0.04em] text-rose-700">一覧で詳細を確認 →</div>
            </div>
          </Link>
        </section>

        <section className="mt-2 border-t border-slate-200 pt-5">
          <div className="mb-4 flex flex-col gap-1">
            <h2 className="text-lg font-semibold tracking-[-0.02em] text-slate-900">直近30日の推移</h2>
            <p className="text-sm text-muted-foreground">
              日次のクリック数とコンバージョン数の変化を確認できます。
            </p>
          </div>
          <OverviewChart data={dailyStats} />
        </section>
      </div>
    </div>
  );
}
