"use client";

import { Button } from "@/components/ui/button";
import { ControlBar } from "@/components/ui/control-bar";
import { Input } from "@/components/ui/input";
import { suspiciousCopy } from "@/copy/suspicious";
import type {
  SuspiciousRiskFilter,
  SuspiciousSortValue,
} from "@/features/suspicious-list/url-state";

const riskButtons: { key: SuspiciousRiskFilter; label: string }[] = [
  { key: "all", label: suspiciousCopy.labels.all },
  { key: "high", label: suspiciousCopy.labels.high },
  { key: "medium", label: suspiciousCopy.labels.medium },
  { key: "low", label: suspiciousCopy.labels.low },
];

interface SuspiciousListControlsProps {
  searchDraft: string;
  resultRange: string;
  risk: SuspiciousRiskFilter;
  sort: SuspiciousSortValue;
  onSearchChange: (value: string) => void;
  onRiskChange: (risk: SuspiciousRiskFilter) => void;
  onSortChange: (sort: SuspiciousSortValue) => void;
}

export function SuspiciousListControls({
  searchDraft,
  resultRange,
  risk,
  sort,
  onSearchChange,
  onRiskChange,
  onSortChange,
}: SuspiciousListControlsProps) {
  return (
    <ControlBar>
      <div className="min-w-0 flex-1">
        <Input
          name="search"
          type="search"
          placeholder={suspiciousCopy.labels.searchPlaceholder}
          aria-label={suspiciousCopy.labels.search}
          value={searchDraft}
          onChange={(event) => onSearchChange(event.target.value)}
          autoComplete="off"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {riskButtons.map((button) => (
          <Button
            key={button.key}
            type="button"
            size="sm"
            variant={risk === button.key ? "default" : "outline"}
            onClick={() => onRiskChange(button.key)}
          >
            {button.label}
          </Button>
        ))}
      </div>

      <select
        className="h-10 border border-input bg-card px-3 text-[13px] text-foreground outline-none transition-colors focus:border-white"
        value={sort}
        onChange={(event) => onSortChange(event.target.value as SuspiciousSortValue)}
        aria-label={suspiciousCopy.labels.sort}
      >
        <option value="count">{suspiciousCopy.labels.sortCount}</option>
        <option value="risk">{suspiciousCopy.labels.sortRisk}</option>
        <option value="latest">{suspiciousCopy.labels.sortLatest}</option>
      </select>

      <div
        aria-label="一覧の件数範囲"
        className="w-full text-[13px] text-foreground/78 sm:ml-auto sm:w-auto"
      >
        {resultRange}
      </div>
    </ControlBar>
  );
}
