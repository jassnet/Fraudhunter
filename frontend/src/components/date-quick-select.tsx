"use client";

import { useMemo } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type QuickDateOption = "latest" | "yesterday" | "today";

const quickDateLabels: Record<QuickDateOption, string> = {
  latest: "最新日",
  today: "今日",
  yesterday: "前日",
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
  const options = useMemo(() => {
    const dates = availableDates || [];
    return dates.map((date) => ({ value: date, label: date }));
  }, [availableDates]);

  return (
    <div className={cn("flex flex-wrap items-center gap-2.5", className)}>
      {showQuickButtons && (
        <div className="flex flex-wrap gap-2">
          {(Object.keys(quickDateLabels) as QuickDateOption[]).map((option) => (
            <Button
              key={option}
              type="button"
              size="sm"
              variant="secondary"
              className="rounded-md border border-slate-200 bg-slate-100 text-slate-700 shadow-none hover:bg-slate-200"
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
      )}
      <select
        className="h-10 rounded-md border border-input bg-white px-4 text-sm shadow-sm outline-none transition focus:border-primary/50"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label="対象日を選択"
      >
        {options.length === 0 ? (
          <option value="" disabled>
            利用可能な日付はありません
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
