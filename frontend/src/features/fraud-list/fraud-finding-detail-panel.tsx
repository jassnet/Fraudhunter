"use client";

import { fraudCopy } from "@/features/fraud-list/copy";
import type { FraudFindingDetailStatus } from "@/features/fraud-list/use-fraud-finding-details";
import type { FraudFindingItem } from "@/lib/api";

interface FraudFindingDetailPanelProps {
  item: FraudFindingItem | null;
  message: string | null;
  status: FraudFindingDetailStatus;
}

function SelectedDetailValue({ value }: { value?: string | null }) {
  return <div>{value?.trim() ? value : "-"}</div>;
}

export function FraudFindingDetailPanel({
  item,
  message,
  status,
}: FraudFindingDetailPanelProps) {
  return (
    <aside className="hidden w-[28rem] shrink-0 border-l border-border bg-card p-4 lg:block">
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
            <div className="text-xs text-muted-foreground">{fraudCopy.labels.details}</div>
            <pre className="overflow-auto rounded border border-border bg-muted/30 p-3 text-xs">
              {JSON.stringify(item.details || {}, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </aside>
  );
}
