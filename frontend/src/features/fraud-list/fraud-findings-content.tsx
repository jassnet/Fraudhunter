"use client";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/ui/state-panel";
import { fraudCopy } from "@/features/fraud-list/copy";
import { FraudFindingsTable } from "@/features/fraud-list/fraud-findings-table";
import { SuspiciousListPagination } from "@/features/suspicious-list/suspicious-list-pagination";
import type { SuspiciousDataStatus } from "@/features/suspicious-list/use-suspicious-data";
import type { FraudFindingItem } from "@/lib/api";

export const FRAUD_FINDINGS_PAGE_SIZE = 20;

interface FraudFindingsContentProps {
  data: FraudFindingItem[];
  message: string | null;
  page: number;
  resultRange: string;
  status: SuspiciousDataStatus;
  totalPages: number;
  onOpenDetail: (item: FraudFindingItem) => void | Promise<void>;
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
    return fraudCopy.states.unauthorizedTitle;
  }

  if (status === "forbidden") {
    return fraudCopy.states.forbiddenTitle;
  }

  if (status === "transient-error") {
    return fraudCopy.states.transientTitle;
  }

  return fraudCopy.states.loadErrorTitle;
}

function getStatePanelMessage(status: SuspiciousDataStatus, message: string | null) {
  if (message) {
    return message;
  }

  if (status === "unauthorized") {
    return fraudCopy.states.unauthorizedMessage;
  }

  if (status === "forbidden") {
    return fraudCopy.states.forbiddenMessage;
  }

  return fraudCopy.states.transientMessage;
}

export function FraudFindingsContent({
  data,
  message,
  page,
  resultRange,
  status,
  totalPages,
  onOpenDetail,
  onPageChange,
  onRetry,
}: FraudFindingsContentProps) {
  if (status === "loading" || status === "refreshing") {
    return (
      <div className="space-y-3">
        <div className="text-sm text-foreground/80">{fraudCopy.states.loadingRange}</div>
        {[...Array(FRAUD_FINDINGS_PAGE_SIZE)].map((_, index) => (
          <Skeleton key={index} className="h-11 w-full" />
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
      <StatePanel
        title={getStatePanelTitle(status)}
        message={getStatePanelMessage(status, message)}
        tone={getStatePanelTone(status)}
        action={
          status === "transient-error" || status === "error" ? (
            <Button variant="outline" onClick={onRetry}>
              {fraudCopy.labels.retry}
            </Button>
          ) : undefined
        }
      />
    );
  }

  if (status === "empty") {
    return (
      <StatePanel
        title={fraudCopy.states.emptyTitle}
        message={fraudCopy.states.emptyMessage}
        tone="neutral"
      />
    );
  }

  return (
    <div className="space-y-3">
      <div className="text-sm text-foreground/80">{resultRange}</div>
      <FraudFindingsTable data={data} onOpenDetail={onOpenDetail} />
      <div className="border-t border-border/70 pt-2">
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
