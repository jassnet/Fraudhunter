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

function getStatePanelProps(status: SuspiciousDataStatus, message: string | null) {
  if (status === "unauthorized") {
    return {
      title: fraudCopy.states.unauthorizedTitle,
      message: message || fraudCopy.states.unauthorizedMessage,
      tone: "neutral" as const,
    };
  }

  if (status === "forbidden") {
    return {
      title: fraudCopy.states.forbiddenTitle,
      message: message || fraudCopy.states.forbiddenMessage,
      tone: "danger" as const,
    };
  }

  if (status === "transient-error") {
    return {
      title: fraudCopy.states.transientTitle,
      message: message || fraudCopy.states.transientMessage,
      tone: "warning" as const,
    };
  }

  return {
    title: fraudCopy.states.loadErrorTitle,
    message: message || fraudCopy.states.loadErrorMessage,
    tone: "neutral" as const,
  };
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
  const statePanelProps = getStatePanelProps(status, message);

  if (status === "loading" || status === "refreshing") {
    return (
      <div className="fc-surface-card-soft p-4">
        <div className="mb-4 text-sm text-foreground/80">{fraudCopy.states.loadingRange}</div>
        <div className="space-y-3">
          {[...Array(FRAUD_FINDINGS_PAGE_SIZE)].map((_, index) => (
            <Skeleton key={index} className="h-11 w-full" />
          ))}
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
      <StatePanel
        title={statePanelProps.title}
        message={statePanelProps.message}
        tone={statePanelProps.tone}
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
    <div className="flex min-w-0 flex-col gap-2">
      <div className="fc-range-bar">
        <div className="fc-meta-copy">
          <div>{fraudCopy.labels.resultRange}</div>
          <div aria-label={fraudCopy.labels.resultRange}>{resultRange}</div>
        </div>
        <div className="text-xs text-foreground/78">
          {fraudCopy.labels.detailHint}
        </div>
      </div>

      <div className="fc-surface-card-soft overflow-hidden">
        <div className="min-w-0 px-0">
          <FraudFindingsTable data={data} onOpenDetail={onOpenDetail} />
        </div>
        <div className="border-t border-border/70 px-4 py-3">
          <SuspiciousListPagination
            page={page}
            totalPages={totalPages}
            resultRange={resultRange}
            onPageChange={onPageChange}
          />
        </div>
      </div>
    </div>
  );
}
