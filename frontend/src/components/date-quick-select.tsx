"use client";

import { useMemo } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type QuickDateOption = "latest" | "yesterday" | "today" | "none";

const quickDateLabels: Record<QuickDateOption, string> = {
  latest: "Latest",
  today: "Today",
  yesterday: "Yesterday",
  none: "Custom",
};

interface DateQuickSelectProps {
  value: string;
  onChange: (value: string) => void;
  availableDates: string[];
  showQuickButtons?: boolean;
  className?: string;
}

const formatDate = (date: Date) => date.toISOString().slice(0, 10);

const getQuickDate = (option: QuickDateOption, dates: string[]) => {
  if (option === "latest") return dates[0] || "";
  if (option === "today") return formatDate(new Date());
  if (option === "yesterday") {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    return formatDate(d);
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
              onClick={() => onChange(getQuickDate(option, availableDates))}
              disabled={option === "latest" && availableDates.length === 0}
            >
              {quickDateLabels[option]}
            </Button>
          ))}
        </div>
      )}
      <select
        className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
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
