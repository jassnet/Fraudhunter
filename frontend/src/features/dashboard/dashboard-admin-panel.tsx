"use client";

import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { dashboardCopy } from "@/features/dashboard/copy";

type AdminCapabilityState = "unknown" | "available" | "unavailable";
type AdminActionType = "refresh" | "master-sync" | null;
type AdminJobUiStatus =
  | "idle"
  | "submitting"
  | "queued"
  | "running"
  | "succeeded"
  | "failed";

interface DashboardAdminPanelProps {
  action: AdminActionType;
  capability: AdminCapabilityState;
  isBusy: boolean;
  status: AdminJobUiStatus;
  onRunMasterSync: () => void | Promise<void>;
  onRunRefresh: () => void | Promise<void>;
}

function resolveAdminStatusTone(status: AdminJobUiStatus) {
  if (status === "running") {
    return "medium" as const;
  }

  if (status === "succeeded") {
    return "low" as const;
  }

  if (status === "failed") {
    return "high" as const;
  }

  return "neutral" as const;
}

function resolveAdminStatusLabel(action: AdminActionType, status: AdminJobUiStatus) {
  if (!action || status === "idle" || status === "submitting") {
    return null;
  }

  const feedback =
    action === "refresh"
      ? dashboardCopy.admin.feedback.refresh
      : dashboardCopy.admin.feedback.masterSync;

  return feedback[status];
}

export function DashboardAdminPanel({
  action,
  capability,
  isBusy,
  status,
  onRunMasterSync,
  onRunRefresh,
}: DashboardAdminPanelProps) {
  if (capability === "available") {
    const statusLabel = resolveAdminStatusLabel(action, status);

    return (
      <div className="fc-surface-card shrink-0 px-3 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="fc-overline font-semibold tracking-[0.12em]">
              {dashboardCopy.admin.title}
            </div>
            <div className="text-[12px] text-foreground/72">
              {dashboardCopy.admin.description}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => void onRunRefresh()}
              disabled={isBusy}
            >
              {dashboardCopy.admin.actions.refresh}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => void onRunMasterSync()}
              disabled={isBusy}
            >
              {dashboardCopy.admin.actions.masterSync}
            </Button>
            {statusLabel ? (
              <StatusBadge tone={resolveAdminStatusTone(status)}>{statusLabel}</StatusBadge>
            ) : null}
          </div>
        </div>
      </div>
    );
  }

  if (capability === "unavailable") {
    return (
      <div className="fc-surface-card-muted shrink-0 px-3 py-3 text-[12px] text-muted-foreground">
        {dashboardCopy.admin.unavailableShortHint}
      </div>
    );
  }

  return null;
}
