"use client";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/ui/state-panel";
import { dashboardCopy } from "@/features/dashboard/copy";
import { suspiciousCopy } from "@/features/suspicious-list/copy";
import { SuspiciousListPagination } from "@/features/suspicious-list/suspicious-list-pagination";
import { SuspiciousListTable } from "@/features/suspicious-list/suspicious-list-table";
import {
  SUSPICIOUS_LIST_PAGE_SIZE,
  type SuspiciousDataStatus,
} from "@/features/suspicious-list/use-suspicious-data";
import type { SuspiciousItem } from "@/lib/api";

interface SuspiciousListContentProps {
  data: SuspiciousItem[];
  groupByReason: boolean;
  message: string | null;
  page: number;
  resultRange: string;
  status: SuspiciousDataStatus;
  totalPages: number;
  onGroupByReasonChange: (checked: boolean) => void;
  onOpenDetail: (item: SuspiciousItem) => void | Promise<void>;
  onPageChange: (page: number) => void;
  onRetry: () => void;
}

function getStatePanelTone(status: SuspiciousDataStatus) {
  if (status === "forbidden") {
    return "danger" as const;
  }

  if (status === "transient-error") {
    return "warning" as const;
  }

  return "neutral" as const;
}

function getStatePanelTitle(status: SuspiciousDataStatus) {
  if (status === "unauthorized") {
    return suspiciousCopy.states.unauthorizedTitle;
  }

  if (status === "forbidden") {
    return suspiciousCopy.states.forbiddenTitle;
  }

  if (status === "transient-error") {
    return suspiciousCopy.states.transientTitle;
  }

  return suspiciousCopy.states.loadErrorTitle;
}

function getStatePanelMessage(status: SuspiciousDataStatus, message: string | null) {
  if (message) {
    return message;
  }

  if (status === "unauthorized") {
    return suspiciousCopy.states.unauthorizedMessage;
  }

  if (status === "forbidden") {
    return suspiciousCopy.states.forbiddenMessage;
  }

  return suspiciousCopy.states.transientMessage;
}

export function SuspiciousListContent({
  data,
  groupByReason,
  message,
  page,
  resultRange,
  status,
  totalPages,
  onGroupByReasonChange,
  onOpenDetail,
  onPageChange,
  onRetry,
}: SuspiciousListContentProps) {
  if (status === "loading" || status === "refreshing") {
    return (
      <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-hidden px-1 py-2 sm:px-2">
        {[...Array(SUSPICIOUS_LIST_PAGE_SIZE)].map((_, index) => (
          <Skeleton key={index} className="h-10 w-full shrink-0" />
        ))}
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
      <div className="min-h-0 flex-1 overflow-auto">
        <StatePanel
          title={getStatePanelTitle(status)}
          message={getStatePanelMessage(status, message)}
          tone={getStatePanelTone(status)}
          action={
            status === "transient-error" || status === "error" ? (
              <Button variant="outline" onClick={onRetry}>
                {dashboardCopy.states.retry}
              </Button>
            ) : undefined
          }
        />
      </div>
    );
  }

  if (status === "empty") {
    return (
      <div className="min-h-0 flex-1 overflow-auto">
        <StatePanel
          title={suspiciousCopy.states.emptyTitle}
          message={suspiciousCopy.states.emptyMessage}
          tone="neutral"
        />
      </div>
    );
  }

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-2 overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border border-border bg-card/70 px-3 py-2.5">
        <div className="min-w-0 space-y-0.5">
          <div className="text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
            {suspiciousCopy.labels.tableDisplayLegend}
          </div>
          <div className="text-[12px] text-foreground/82">{resultRange}</div>
        </div>
        <label className="inline-flex cursor-pointer select-none items-center gap-2 text-[12px] text-foreground/90">
          <input
            type="checkbox"
            className="h-3.5 w-3.5 shrink-0 rounded border-input accent-primary"
            checked={groupByReason}
            onChange={(event) => onGroupByReasonChange(event.target.checked)}
          />
          <span className="whitespace-nowrap">
            {suspiciousCopy.labels.groupByReasonPattern}
          </span>
        </label>
      </div>

      <SuspiciousListTable
        data={data}
        onOpenDetail={onOpenDetail}
        groupByReason={groupByReason}
      />

      <div className="shrink-0">
        <SuspiciousListPagination
          page={page}
          totalPages={totalPages}
          resultRange={resultRange}
          onPageChange={onPageChange}
        />
      </div>
    </div>
  );
}
