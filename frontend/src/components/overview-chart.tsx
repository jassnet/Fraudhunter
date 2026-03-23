"use client";

import { useState } from "react";
import { DailyStatsItem } from "@/lib/api";
import { cn } from "@/lib/utils";

const safeNumber = (value?: number) => (Number.isFinite(value) ? value ?? 0 : 0);

const formatDate = (dateStr: string) => {
  const match = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return dateStr;
  return `${parseInt(match[2])}/${parseInt(match[3])}`;
};

export function OverviewChart({
  data,
  className,
}: {
  data: DailyStatsItem[];
  className?: string;
}) {
  const [expanded, setExpanded] = useState(false);

  if (!data || data.length === 0) {
    return (
      <div
        className={cn(
          "flex h-[280px] items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-sm text-muted-foreground",
          className
        )}
      >
        表示できるデータはありません
      </div>
    );
  }

  const allRows = data.slice(-30);
  const visibleRows = expanded ? allRows : allRows.slice(-7);
  const hiddenCount = allRows.length - visibleRows.length;
  const max = Math.max(
    ...allRows.map((d) => Math.max(safeNumber(d.clicks), safeNumber(d.conversions), 1))
  );

  return (
    <div className={cn("rounded-xl border border-slate-200 bg-slate-50 p-4 sm:p-5", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <p className="text-sm font-medium text-slate-800">推移チャート</p>
          <p className="mt-1 text-xs text-muted-foreground">
            クリック数と CV 数の相対的な増減を一覧で比較します。
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-slate-800" />
            クリック数
          </span>
          <span className="inline-flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            CV 数
          </span>
        </div>
      </div>
      <div className="mt-4 space-y-3">
      {visibleRows.map((row) => {
        const clickVal = safeNumber(row.clicks);
        const convVal = safeNumber(row.conversions);
        const clickPct = Math.round((clickVal / max) * 100);
        const convPct = Math.round((convVal / max) * 100);
        return (
          <div
            key={row.date}
            className="grid grid-cols-[72px_minmax(0,1fr)_96px] items-center gap-4 rounded-lg border border-transparent bg-white px-3 py-3 sm:grid-cols-[88px_minmax(0,1fr)_112px] sm:px-4"
          >
            <div className="text-xs font-medium text-slate-600">{formatDate(row.date)}</div>
            <div className="space-y-2">
              <div className="h-2 rounded-full bg-slate-200">
                <div className="h-2 rounded-full bg-slate-800" style={{ width: `${clickPct}%` }} />
              </div>
              <div className="h-2 rounded-full bg-slate-200">
                <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${convPct}%` }} />
              </div>
            </div>
            <div className="text-right text-[11px] leading-5 text-slate-500 sm:text-xs">
              <div>CL {clickVal.toLocaleString()}</div>
              <div>CV {convVal.toLocaleString()}</div>
            </div>
          </div>
        );
      })}
      </div>
      {hiddenCount > 0 && (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="mt-3 w-full rounded-lg border border-slate-200 bg-white py-2 text-xs text-slate-500 hover:bg-slate-50 hover:text-slate-700"
        >
          過去の推移を表示（+{hiddenCount}日）
        </button>
      )}
      {expanded && allRows.length > 7 && (
        <button
          type="button"
          onClick={() => setExpanded(false)}
          className="mt-2 w-full rounded-lg border border-slate-200 bg-white py-2 text-xs text-slate-500 hover:bg-slate-50 hover:text-slate-700"
        >
          折りたたむ
        </button>
      )}
    </div>
  );
}
