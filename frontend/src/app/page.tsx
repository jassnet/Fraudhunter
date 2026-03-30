"use client";

import { useMemo } from "react";
import { DashboardDiagnostics } from "@/components/dashboard-diagnostics";
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

  const actions = (
    <>
      {adminActions.capability === "available" ? (
        <div className="flex items-center gap-2 border border-border bg-card px-2 py-2">
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
      ) : adminActions.capability === "unavailable" ? (
        <p className="max-w-xl border border-border bg-card px-2 py-2 text-[12px] text-muted-foreground">
          {dashboardCopy.admin.unavailableHint}
        </p>
      ) : null}
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
            <div className="grid gap-3 lg:grid-cols-4">
              {[...Array(4)].map((_, index) => (
                <div key={index} className="border border-border p-4">
                  <Skeleton className="h-3 w-20" />
                  <Skeleton className="mt-5 h-12 w-28" />
                  <Skeleton className="mt-6 h-3 w-32" />
                </div>
              ))}
            </div>
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
          <DashboardSummaryMetrics summary={summary} />
          <DashboardDiagnostics diagnostics={diagnostics} />
          <SectionFrame title={dashboardCopy.labels.chart}>
            <OverviewChart data={dailyStats} />
          </SectionFrame>
        </div>
      </div>
    </div>
  );
}
