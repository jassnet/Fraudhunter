"use client";

import { Button } from "@/components/ui/button";
import { fraudCopy } from "@/features/fraud-list/copy";
import { buildFraudDetailMetrics } from "@/features/fraud-list/fraud-finding-metrics";
import type { FraudFindingDetailStatus } from "@/features/fraud-list/use-fraud-finding-details";
import type { FraudFindingItem } from "@/lib/api";
import { cn } from "@/lib/utils";

interface FraudFindingDetailPanelProps {
  className?: string;
  item: FraudFindingItem | null;
  message: string | null;
  onClose?: () => void;
  status: FraudFindingDetailStatus;
}

function SelectedDetailValue({ value }: { value?: string | null }) {
  return <div>{value?.trim() ? value : "-"}</div>;
}

export function FraudFindingDetailPanel({
  className,
  item,
  message,
  onClose,
  status,
}: FraudFindingDetailPanelProps) {
  const detailMetrics = buildFraudDetailMetrics(item?.details);

  return (
    <aside className={cn("fc-surface-card-soft min-w-0 p-4", className)}>
      <div className="mb-4 flex items-start justify-between gap-3 border-b border-border/70 pb-3">
        <div className="min-w-0">
          <div className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
            {fraudCopy.labels.detailPanelTitle}
          </div>
          <div className="mt-1 text-sm text-foreground/80">
            {item ? fraudCopy.labels.detail : fraudCopy.labels.detailPlaceholder}
          </div>
        </div>
        {onClose ? (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={onClose}
            className="h-8 shrink-0 px-2 text-xs text-muted-foreground hover:text-foreground"
          >
            {fraudCopy.labels.closeDetail}
          </Button>
        ) : null}
      </div>

      {!item ? (
        <div className="text-sm text-muted-foreground">{fraudCopy.labels.detailPlaceholder}</div>
      ) : status === "loading" ? (
        <div className="text-sm text-muted-foreground">{fraudCopy.states.loadingRange}</div>
      ) : status === "error" ? (
        <div className="space-y-2 text-sm">
          <div className="font-medium text-destructive">{fraudCopy.states.detailError}</div>
          <div className="text-muted-foreground">{message || fraudCopy.states.detailError}</div>
        </div>
      ) : (
        <div className="space-y-3 text-sm">
          <div>
            <div className="text-xs text-muted-foreground">{fraudCopy.labels.user}</div>
            <SelectedDetailValue value={item.user_name} />
          </div>
          <div>
            <div className="text-xs text-muted-foreground">{fraudCopy.labels.media}</div>
            <SelectedDetailValue value={item.media_name} />
          </div>
          <div>
            <div className="text-xs text-muted-foreground">{fraudCopy.labels.promotion}</div>
            <SelectedDetailValue value={item.promotion_name} />
          </div>
          <div>
            <div className="text-xs text-muted-foreground">{fraudCopy.labels.reasons}</div>
            <ul className="list-disc pl-5">
              {(item.reasons_formatted || []).map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
          <div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <div className="text-xs text-muted-foreground">{fraudCopy.labels.firstDetected}</div>
                <SelectedDetailValue value={item.first_time} />
              </div>
              <div>
                <div className="text-xs text-muted-foreground">{fraudCopy.labels.lastDetected}</div>
                <SelectedDetailValue value={item.last_time} />
              </div>
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">{fraudCopy.labels.details}</div>
            {detailMetrics.length > 0 ? (
              <dl className="grid gap-x-3 gap-y-2 rounded border border-border bg-muted/20 p-3 sm:grid-cols-2">
                {detailMetrics.map((metric) => (
                  <div key={metric.key}>
                    <dt className="text-xs text-muted-foreground">{metric.label}</dt>
                    <dd className="mt-0.5 text-sm text-foreground">{metric.value}</dd>
                  </div>
                ))}
              </dl>
            ) : (
              <div className="text-sm text-muted-foreground">{fraudCopy.labels.detailsEmpty}</div>
            )}
          </div>
        </div>
      )}
    </aside>
  );
}
