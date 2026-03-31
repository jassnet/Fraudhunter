"use client";

import { useMemo } from "react";
import { Button } from "@/components/ui/button";
import { dashboardCopy } from "@/copy/dashboard";
import { cn } from "@/lib/utils";

interface LastUpdatedProps {
  lastUpdated: Date | null;
  onRefresh: () => void;
  isRefreshing?: boolean;
  className?: string;
  /** true のとき再読み込みはアイコンのみ（一覧ヘッダー用） */
  compact?: boolean;
}

const formatTime = (date: Date) =>
  date.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });

export function LastUpdated({
  lastUpdated,
  onRefresh,
  isRefreshing = false,
  className,
  compact = false,
}: LastUpdatedProps) {
  const timeLabel = useMemo(() => (lastUpdated ? formatTime(lastUpdated) : "-"), [lastUpdated]);
  const actionLabel = dashboardCopy.states.refresh;

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-x-2 gap-y-1.5 text-[13px] text-foreground/85",
        className
      )}
    >
      <span>最終更新 {timeLabel}</span>
      {compact ? (
        <Button
          type="button"
          size="icon"
          variant="ghost"
          onClick={onRefresh}
          disabled={isRefreshing}
          aria-label={actionLabel}
          className="h-8 w-8 shrink-0 text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <span className="text-[15px] leading-none" aria-hidden>
            ↻
          </span>
        </Button>
      ) : (
        <Button size="sm" variant="outline" onClick={onRefresh} disabled={isRefreshing}>
          {actionLabel}
        </Button>
      )}
      {isRefreshing ? (
        <span aria-live="polite" className="text-xs text-foreground/78">
          {dashboardCopy.states.refreshing}
        </span>
      ) : null}
    </div>
  );
}
