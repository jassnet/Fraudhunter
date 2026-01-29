"use client";

import { useMemo, useRef } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type QuickDateOption = "latest" | "yesterday" | "today" | "none";

const quickDateLabels: Record<QuickDateOption, string> = {
  latest: "Latest",
  today: "Today",
  yesterday: "Yesterday",
  none: "Pick date",
};

interface DateQuickSelectProps {
  value: string;
  onChange: (value: string) => void;
  availableDates: string[];
  showQuickButtons?: boolean;
  className?: string;
}

const formatDate = (date: Date) => date.toISOString().slice(0, 10);

const pickAvailableDate = (candidate: string, dates: string[]) => {
  if (!dates.length) return "";
  return dates.includes(candidate) ? candidate : dates[0];
};

const getQuickDate = (option: QuickDateOption, dates: string[]) => {
  if (option === "latest") return dates[0] || "";
  if (option === "today") return pickAvailableDate(formatDate(new Date()), dates);
  if (option === "yesterday") {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    return pickAvailableDate(formatDate(d), dates);
  }
  return "";
};

export function DateQuickSelect({
  value,
  onChange,
  availableDates,
  showQuickButtons = true,
  className,
}: DateQuickSelectProps) {
  const selectRef = useRef<HTMLSelectElement>(null);
  const options = useMemo(() => {
    const dates = availableDates || [];
    return dates.map((date) => ({ value: date, label: date }));
  }, [availableDates]);

  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      {showQuickButtons && (
        <div className="flex flex-wrap gap-2">
          {(Object.keys(quickDateLabels) as QuickDateOption[]).map((option) => (
            <Button
              key={option}
              type="button"
              size="sm"
              variant={option === "none" ? "outline" : "secondary"}
              onClick={() => {
                if (option === "none") {
                  selectRef.current?.focus();
                  return;
                }
                const nextDate = getQuickDate(option, availableDates);
                if (nextDate) onChange(nextDate);
              }}
              disabled={option !== "none" && availableDates.length === 0}
            >
              {quickDateLabels[option]}
            </Button>
          ))}
        </div>
      )}
      <select
        ref={selectRef}
        className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label="Select date"
      >
        {options.length === 0 ? (
          <option value="" disabled>
            No dates
          </option>
        ) : (
          options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))
        )}
      </select>
    </div>
  );
}
