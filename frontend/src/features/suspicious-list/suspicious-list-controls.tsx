"use client";

import { suspiciousCopy } from "@/features/suspicious-list/copy";
import { cn } from "@/lib/utils";
import type { SuspiciousRiskFilter, SuspiciousSortValue } from "./url-state";

const selectClass = "fc-compact-select";

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
    <div className="fc-surface-card-soft fc-toolbar text-sm">
      <div className="fc-toolbar-section">
        <span className="fc-overline">
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

      <div className="fc-toolbar-section fc-toolbar-section-split">
        <span className="fc-overline">
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
