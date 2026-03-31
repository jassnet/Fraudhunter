"use client";

import type { ReactNode } from "react";
import { useMemo } from "react";
import { DashboardSummaryMetrics } from "@/components/dashboard-summary-metrics";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { OverviewChart } from "@/components/overview-chart";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { SectionFrame } from "@/components/ui/section-frame";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/ui/state-panel";
import { StatusBadge } from "@/components/ui/status-badge";
import { dashboardCopy } from "@/copy/dashboard";
import { useAdminJobActions } from "@/features/admin-actions/use-admin-job-actions";
import { useDashboardData } from "@/hooks/use-dashboard-data";

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

  const adminActions = useAdminJobActions({ onSuccess: handleRefresh });
  const adminStatusTone = useMemo<"neutral" | "medium" | "low" | "high">(() => {
    if (adminActions.status === "running") return "medium";
    if (adminActions.status === "succeeded") return "low";
    if (adminActions.status === "failed") return "high";
    return "neutral";
  }, [adminActions.status]);
  const adminStatusLabel = useMemo(() => {
    if (!adminActions.action) return null;
    if (adminActions.status === "idle" || adminActions.status === "submitting") return null;
    const feedback =
      adminActions.action === "refresh"
        ? dashboardCopy.admin.feedback.refresh
        : dashboardCopy.admin.feedback.masterSync;
    return feedback[adminActions.status];
  }, [adminActions.action, adminActions.status]);

  const headerActions = (
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

  const adminPanel =
    adminActions.capability === "available" ? (
      <div className="shrink-0 border border-border bg-card px-3 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
              管理者操作
            </div>
            <div className="text-[12px] text-foreground/72">
              直近データの再取得とマスタ同期をここで実行できます。
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => void adminActions.runRefresh()}
              disabled={adminActions.isBusy}
            >
              {dashboardCopy.admin.actions.refresh}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => void adminActions.runMasterSync()}
              disabled={adminActions.isBusy}
            >
              {dashboardCopy.admin.actions.masterSync}
            </Button>
            {adminStatusLabel ? (
              <StatusBadge tone={adminStatusTone}>{adminStatusLabel}</StatusBadge>
            ) : null}
          </div>
        </div>
      </div>
    ) : adminActions.capability === "unavailable" ? (
      <div className="shrink-0 border border-dashed border-border bg-card/55 px-3 py-3 text-[12px] text-muted-foreground">
        {dashboardCopy.admin.unavailableShortHint}
      </div>
    ) : null;

  const headerStatus =
    diagnostics.findingsStale && summary ? (
      <div className="text-[12px] text-[hsl(var(--warning))]">
        {dashboardCopy.states.staleTitle}
      </div>
    ) : null;

  const dashboardBodyShell = (children: ReactNode) => (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden px-3 py-2 sm:px-4 sm:py-3">
      {children}
    </div>
  );

  if (status === "loading" || status === "refreshing") {
    return (
      <div className="flex h-full min-h-0 flex-col overflow-hidden">
        <PageHeader
          title={dashboardCopy.title}
          meta={dashboardCopy.loadingMeta}
          actions={headerActions}
          status={headerStatus}
          className="shrink-0"
        />
        {dashboardBodyShell(
          <>
            <div className="shrink-0">
              {adminPanel}
            </div>
            <div className="shrink-0">
              <div className="grid border border-border bg-card md:grid-cols-2 xl:grid-cols-3">
                {[...Array(3)].map((_, index) => (
                  <div key={index} className="min-h-[100px] border-t border-border p-3 first:border-t-0 md:first:border-t md:odd:border-r xl:border-t-0 xl:border-r xl:last:border-r-0">
                    <Skeleton className="h-3 w-20" />
                    <Skeleton className="mt-3 h-9 w-24" />
                    <Skeleton className="mt-3 h-3 w-32" />
                  </div>
                ))}
              </div>
            </div>
            <SectionFrame
              title={dashboardCopy.labels.chart}
              className="flex min-h-0 flex-1 flex-col overflow-hidden"
              bodyClassName="flex min-h-0 flex-1 flex-col overflow-hidden p-3 sm:p-4"
            >
              <Skeleton className="min-h-[12rem] flex-1 rounded-none" />
            </SectionFrame>
          </>
        )}
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
        <PageHeader title={dashboardCopy.title} actions={headerActions} />
        <div className="min-h-0 flex-1 overflow-auto p-4 sm:p-6">
          <StatePanel
            title={
              status === "unauthorized"
                ? dashboardCopy.states.unauthorizedTitle
                : status === "forbidden"
                  ? dashboardCopy.states.forbiddenTitle
                : status === "transient-error"
                    ? dashboardCopy.states.transientTitle
                    : dashboardCopy.states.genericErrorTitle
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
        <PageHeader title={dashboardCopy.title} actions={headerActions} />
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

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <PageHeader
        title={dashboardCopy.title}
        meta={dashboardCopy.targetDateLabel(summary.date)}
        actions={headerActions}
        status={headerStatus}
        className="shrink-0"
      />

      {dashboardBodyShell(
        <>
          {adminPanel}
          <div className="shrink-0">
            <DashboardSummaryMetrics summary={summary} compact />
          </div>
          <SectionFrame
            title={dashboardCopy.labels.chart}
            className="flex min-h-0 flex-1 flex-col overflow-hidden"
            bodyClassName="flex min-h-0 flex-1 flex-col overflow-hidden p-3 sm:p-4"
          >
            <OverviewChart data={dailyStats} layout="fill" />
          </SectionFrame>
        </>
      )}
    </div>
  );
}
