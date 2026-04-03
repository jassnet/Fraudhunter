"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { suspiciousCopy } from "@/features/suspicious-list/copy";
import { SuspiciousRowDetails } from "@/features/suspicious-list/suspicious-row-details";
import type { SuspiciousDetailStatus } from "@/features/suspicious-list/use-suspicious-details";
import type { SuspiciousItem } from "@/lib/api";

interface SuspiciousDetailDrawerProps {
  detailError: string | null;
  item: SuspiciousItem;
  itemKey: string;
  status: SuspiciousDetailStatus;
  onClose: () => void;
}

export function SuspiciousDetailDrawer({
  detailError,
  item,
  itemKey,
  status,
  onClose,
}: SuspiciousDetailDrawerProps) {
  useEffect(() => {
    const handleKeydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeydown);
    return () => window.removeEventListener("keydown", handleKeydown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto overscroll-contain"
      role="dialog"
      aria-modal="true"
      aria-label={suspiciousCopy.labels.detailPanelTitle}
    >
      <div className="relative flex min-h-[100dvh] min-w-full justify-end">
        <button
          type="button"
          className="fc-detail-drawer-backdrop absolute inset-0 z-0"
          onClick={onClose}
          aria-label={suspiciousCopy.labels.closeDetailPanelBackdrop}
        />
        <aside className="fc-detail-drawer-panel relative z-10 flex min-h-[100dvh] w-full max-w-[40rem] shrink-0 flex-col overflow-x-hidden border-l border-border bg-card text-card-foreground shadow-2xl sm:rounded-l-2xl">
          <div className="flex shrink-0 items-center justify-between gap-3 border-b border-border bg-card px-3 py-2.5 sm:px-4">
            <div className="min-w-0">
              <div className="text-xs font-semibold tracking-tight text-foreground">
                {suspiciousCopy.labels.detailBreadcrumb}
              </div>
              <div className="mt-0.5 text-[11px] leading-snug text-muted-foreground">
                {suspiciousCopy.labels.detailEscapeHint}
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-8 shrink-0 border-border bg-transparent hover:bg-muted"
              onClick={onClose}
              aria-label={suspiciousCopy.labels.backToList}
            >
              {suspiciousCopy.labels.backToList}
            </Button>
          </div>
          <div className="fc-detail-drawer-panel-body flex flex-1 flex-col bg-card px-3 py-3 sm:px-4">
            <SuspiciousRowDetails
              key={itemKey}
              item={item}
              status={status}
              detailError={detailError}
              variant="panel"
            />
          </div>
        </aside>
      </div>
    </div>
  );
}
