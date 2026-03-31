"use client";

import { suspiciousCopy } from "@/features/suspicious-list/copy";
import { cn } from "@/lib/utils";
import type { SuspiciousRiskFilter, SuspiciousSortValue } from "./url-state";

const selectClass =
  "h-8 min-w-[6.5rem] rounded-md border border-input bg-background px-2 text-[12px] text-foreground outline-none transition-[color,box-shadow,border-color] focus-visible:border-ring focus-visible:ring-1 focus-visible:ring-ring/40";

interface SuspiciousListControlsProps {
  risk: SuspiciousRiskFilter;
  sort: SuspiciousSortValue;
  onRiskChange: (risk: SuspiciousRiskFilter) => void;
  onSortChange: (sort: SuspiciousSortValue) => void;
}

export function SuspiciousListControls({
  risk,
  sort,
  onRiskChange,
  onSortChange,
}: SuspiciousListControlsProps) {
  return (
    <div className="flex flex-col gap-3 border border-border bg-card/70 px-3 py-3 text-sm text-foreground/90 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 flex-wrap items-center gap-2">
        <span className="shrink-0 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
          {suspiciousCopy.labels.listFiltersLegend}
        </span>
        <select
          className={selectClass}
          value={risk}
          onChange={(event) => onRiskChange(event.target.value as SuspiciousRiskFilter)}
          aria-label={suspiciousCopy.labels.riskFilter}
        >
          <option value="all">{suspiciousCopy.labels.all}</option>
          <option value="high">{suspiciousCopy.labels.high}</option>
          <option value="medium">{suspiciousCopy.labels.medium}</option>
          <option value="low">{suspiciousCopy.labels.low}</option>
        </select>
      </div>

      <div className="flex min-w-0 flex-wrap items-center gap-2 border-t border-border/70 pt-3 sm:border-l sm:border-t-0 sm:pl-3 sm:pt-0">
        <span className="shrink-0 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
          {suspiciousCopy.labels.sort}
        </span>
        <select
          className={cn(selectClass, "min-w-[9.5rem] sm:min-w-[10.5rem]")}
          value={sort}
          onChange={(event) => onSortChange(event.target.value as SuspiciousSortValue)}
          aria-label={suspiciousCopy.labels.sort}
        >
          <option value="count">{suspiciousCopy.labels.sortCount}</option>
          <option value="risk">{suspiciousCopy.labels.sortRisk}</option>
          <option value="latest">{suspiciousCopy.labels.sortLatest}</option>
        </select>
      </div>
    </div>
  );
}
