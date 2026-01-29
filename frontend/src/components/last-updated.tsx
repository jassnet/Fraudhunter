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
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold">
        Last updated: {timeLabel}
      </span>

      <Button size="sm" variant="outline" onClick={onRefresh} disabled={isRefreshing}>
        Refresh
      </Button>

      {isRefreshing ? (
        <span className="text-xs text-muted-foreground" aria-live="polite">
          Updating...
        </span>
      ) : null}
    </div>
  );
}
