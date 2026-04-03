"use client";

import type { ReactNode } from "react";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/ui/state-panel";
import { useAdminJobActions } from "@/features/admin-actions/use-admin-job-actions";
import {
  DashboardAdminPanel,
} from "@/features/dashboard/dashboard-admin-panel";
import {
  DashboardChartCard,
  DashboardChartSkeleton,
} from "@/features/dashboard/dashboard-chart-card";
import { dashboardCopy } from "@/features/dashboard/copy";
import { DashboardSummaryMetrics } from "@/features/dashboard/dashboard-summary-metrics";
import { OverviewChart } from "@/features/dashboard/overview-chart";
import { useDashboardData } from "@/features/dashboard/use-dashboard-data";

function dashboardBodyShell(children: ReactNode) {
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden px-3 py-2 sm:px-4 sm:py-3">
      {children}
    </div>
  );
}

function getStatePanelTitle(status: "unauthorized" | "forbidden" | "transient-error" | "error") {
  if (status === "unauthorized") {
    return dashboardCopy.states.unauthorizedTitle;
  }

  if (status === "forbidden") {
    return dashboardCopy.states.forbiddenTitle;
  }

  if (status === "transient-error") {
    return dashboardCopy.states.transientTitle;
  }

  return dashboardCopy.states.genericErrorTitle;
}

function getStatePanelTone(status: "unauthorized" | "forbidden" | "transient-error" | "error") {
  if (status === "forbidden") {
    return "danger" as const;
  }

  if (status === "transient-error") {
    return "warning" as const;
  }

  return "neutral" as const;
}

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

  const headerStatus =
    diagnostics.findingsStale && summary ? (
      <div className="text-[12px] text-[hsl(var(--warning))]">
        {dashboardCopy.states.staleTitle}
      </div>
    ) : null;

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
            <DashboardAdminPanel
              action={adminActions.action}
              capability={adminActions.capability}
              isBusy={adminActions.isBusy}
              status={adminActions.status}
              onRunRefresh={adminActions.runRefresh}
              onRunMasterSync={adminActions.runMasterSync}
            />
            <div className="shrink-0">
              <div className="grid border border-border bg-card md:grid-cols-2 xl:grid-cols-3">
                {[...Array(3)].map((_, index) => (
                  <div
                    key={index}
                    className="min-h-[100px] border-t border-border p-3 first:border-t-0 md:first:border-t md:odd:border-r xl:border-t-0 xl:border-r xl:last:border-r-0"
                  >
                    <Skeleton className="h-3 w-20" />
                    <Skeleton className="mt-3 h-9 w-24" />
                    <Skeleton className="mt-3 h-3 w-32" />
                  </div>
                ))}
              </div>
            </div>
            <DashboardChartSkeleton />
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
            title={getStatePanelTitle(status)}
            message={message || dashboardCopy.states.loadError}
            tone={getStatePanelTone(status)}
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
          <DashboardAdminPanel
            action={adminActions.action}
            capability={adminActions.capability}
            isBusy={adminActions.isBusy}
            status={adminActions.status}
            onRunRefresh={adminActions.runRefresh}
            onRunMasterSync={adminActions.runMasterSync}
          />
          <div className="shrink-0">
            <DashboardSummaryMetrics summary={summary} compact />
          </div>
          <DashboardChartCard>
            <OverviewChart data={dailyStats} layout="fill" />
          </DashboardChartCard>
        </>
      )}
    </div>
  );
}
