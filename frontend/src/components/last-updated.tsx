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
  date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });

export function LastUpdated({
  lastUpdated,
  onRefresh,
  isRefreshing = false,
  className,
}: LastUpdatedProps) {
  const timeLabel = useMemo(() => {
    if (!lastUpdated) return "-";
    return formatTime(lastUpdated);
  }, [lastUpdated]);

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <span className="text-sm text-slate-500">
        最終更新: {timeLabel}
      </span>

      <Button
        size="sm"
        variant="outline"
        onClick={onRefresh}
        disabled={isRefreshing}
      >
        再読み込み
      </Button>

      {isRefreshing ? (
        <span className="text-xs text-muted-foreground" aria-live="polite">
          更新しています...
        </span>
      ) : null}
    </div>
  );
}
