"use client";

import { useMemo } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type QuickDateOption = "latest" | "yesterday" | "today";

const quickDateLabels: Record<QuickDateOption, string> = {
  latest: "最新",
  today: "今日",
  yesterday: "昨日",
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
  const date = new Date();
  date.setDate(date.getDate() - 1);
  return pickAvailableDate(formatDate(date), dates);
};

export function DateQuickSelect({
  value,
  onChange,
  availableDates,
  showQuickButtons = true,
  className,
}: DateQuickSelectProps) {
  const options = useMemo(
    () => (availableDates || []).map((date) => ({ value: date, label: date })),
    [availableDates]
  );

  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      {showQuickButtons ? (
        <div className="flex flex-wrap gap-2">
          {(Object.keys(quickDateLabels) as QuickDateOption[]).map((option) => (
            <Button
              key={option}
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                const nextDate = getQuickDate(option, availableDates);
                if (nextDate) onChange(nextDate);
              }}
              disabled={availableDates.length === 0}
            >
              {quickDateLabels[option]}
            </Button>
          ))}
        </div>
      ) : null}

      <select
        className="h-10 min-w-[9rem] rounded-[var(--radius)] border border-input bg-card px-3 text-[13px] text-foreground outline-none transition-[color,box-shadow,border-color] focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/45 disabled:cursor-not-allowed disabled:opacity-40"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-label="対象日"
      >
        {options.length === 0 ? (
          <option value="" disabled>
            利用可能な日付がありません
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
