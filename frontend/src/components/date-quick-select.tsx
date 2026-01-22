"use client";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar, ChevronLeft, ChevronRight } from "lucide-react";
import { useMemo } from "react";
import { cn } from "@/lib/utils";

interface DateQuickSelectProps {
  value: string;
  onChange: (date: string) => void;
  availableDates?: string[];
  showQuickButtons?: boolean;
  className?: string;
}

type QuickDateOption = "today" | "yesterday" | "2days" | "3days" | "week";

const quickDateLabels: Record<QuickDateOption, string> = {
  today: "今日",
  yesterday: "昨日",
  "2days": "2日前",
  "3days": "3日前",
  week: "1週間前",
};

function formatDateJa(dateStr: string): string {
  const date = new Date(dateStr);
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const weekdays = ["日", "月", "火", "水", "木", "金", "土"];
  const weekday = weekdays[date.getDay()];
  return `${month}/${day} (${weekday})`;
}

function getDateOffset(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().split("T")[0];
}

export function DateQuickSelect({
  value,
  onChange,
  availableDates = [],
  showQuickButtons = true,
  className = "",
}: DateQuickSelectProps) {
  // クイック選択の日付を計算
  const quickDates = useMemo(
    () => ({
      today: getDateOffset(0),
      yesterday: getDateOffset(1),
      "2days": getDateOffset(2),
      "3days": getDateOffset(3),
      week: getDateOffset(7),
    }),
    []
  );

  // 現在選択中のクイックオプションを判定
  const currentQuickOption = useMemo(() => {
    for (const [key, date] of Object.entries(quickDates)) {
      if (date === value) return key as QuickDateOption;
    }
    return null;
  }, [value, quickDates]);

  // 利用可能な日付かチェック
  const isDateAvailable = (date: string) => {
    if (availableDates.length === 0) return true;
    return availableDates.includes(date);
  };

  // 前後の日付に移動
  const navigateDate = (direction: "prev" | "next") => {
    if (!value || availableDates.length === 0) return;
    
    const currentIndex = availableDates.indexOf(value);
    if (currentIndex === -1) return;
    
    const newIndex = direction === "prev" ? currentIndex + 1 : currentIndex - 1;
    if (newIndex >= 0 && newIndex < availableDates.length) {
      onChange(availableDates[newIndex]);
    }
  };

  const canGoPrev = availableDates.length > 0 && availableDates.indexOf(value) < availableDates.length - 1;
  const canGoNext = availableDates.length > 0 && availableDates.indexOf(value) > 0;

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {/* クイック選択ボタン */}
      {showQuickButtons && (
        <div className="hidden lg:flex items-center gap-1 mr-2">
          {(["today", "yesterday", "2days", "3days"] as QuickDateOption[]).map((option) => {
            const dateValue = quickDates[option];
            const available = isDateAvailable(dateValue);
            const isActive = currentQuickOption === option;
            
            return (
              <Button
                key={option}
                variant={isActive ? "default" : "outline"}
                size="sm"
                onClick={() => onChange(dateValue)}
                disabled={!available}
                className={cn(
                  "h-8 px-2 text-xs",
                  !available && "opacity-50",
                  isActive && "bg-primary text-primary-foreground"
                )}
              >
                {quickDateLabels[option]}
              </Button>
            );
          })}
        </div>
      )}

      {/* 日付ナビゲーション */}
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon"
          className="size-8"
          onClick={() => navigateDate("prev")}
          disabled={!canGoPrev}
          aria-label="前の日付へ移動"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        <Select value={value} onValueChange={onChange}>
          <SelectTrigger className="w-[160px] h-8">
            <Calendar className="mr-2 h-4 w-4" />
            <SelectValue placeholder="日付を選択">
              {value ? formatDateJa(value) : "日付を選択"}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {availableDates.length > 0 ? (
              availableDates.map((d) => (
                <SelectItem key={d} value={d}>
                  <div className="flex items-center justify-between w-full">
                    <span>{formatDateJa(d)}</span>
                    <span className="text-xs text-muted-foreground ml-2">{d}</span>
                  </div>
                </SelectItem>
              ))
            ) : (
              <SelectItem value={value || "none"} disabled>
                データがありません
              </SelectItem>
            )}
          </SelectContent>
        </Select>

        <Button
          variant="outline"
          size="icon"
          className="size-8"
          onClick={() => navigateDate("next")}
          disabled={!canGoNext}
          aria-label="次の日付へ移動"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
