"use client";

import { useMemo } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface LastUpdatedProps {
  lastUpdated: Date | null;
  onRefresh: () => void;
  isRefreshing?: boolean;
  className?: string;
}

const formatTime = (date: Date) =>
  date.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });

export function LastUpdated({
  lastUpdated,
  onRefresh,
  isRefreshing = false,
  className,
}: LastUpdatedProps) {
  const timeLabel = useMemo(() => (lastUpdated ? formatTime(lastUpdated) : "-"), [lastUpdated]);

  return (
    <div className={cn("flex items-center gap-2 text-xs text-muted-foreground", className)}>
      <span>最終更新 {timeLabel}</span>
      <Button size="sm" variant="outline" onClick={onRefresh} disabled={isRefreshing}>
        再読込
      </Button>
      {isRefreshing ? (
        <span aria-live="polite" className="text-[11px] uppercase tracking-[0.14em]">
          更新中
        </span>
      ) : null}
    </div>
  );
}
