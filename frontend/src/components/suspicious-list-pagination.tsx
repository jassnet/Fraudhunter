"use client";

import { Button } from "@/components/ui/button";
import { suspiciousCopy } from "@/copy/suspicious";

interface SuspiciousListPaginationProps {
  page: number;
  totalPages: number;
  resultRange: string;
  onPageChange: (page: number) => void;
}

export function SuspiciousListPagination({
  page,
  totalPages,
  resultRange,
  onPageChange,
}: SuspiciousListPaginationProps) {
  const canPrev = page > 1;
  const canNext = page < totalPages;

  return (
    <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 py-1 text-[12px] text-foreground/78">
      <div aria-label="表示件数" aria-live="polite" className="tabular-nums text-foreground/86">
        {resultRange}
      </div>
      <div className="flex items-center gap-1">
        <Button
          type="button"
          size="sm"
          variant="ghost"
          className="h-7 px-2 text-[12px]"
          onClick={() => onPageChange(1)}
          disabled={!canPrev}
        >
          {suspiciousCopy.pagination.first}
        </Button>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          className="h-7 px-2 text-[12px]"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={!canPrev}
        >
          {suspiciousCopy.pagination.prev}
        </Button>
        <span className="min-w-[3.5rem] text-center tabular-nums text-[12px] font-medium text-foreground/90">
          {page} / {totalPages}
        </span>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          className="h-7 px-2 text-[12px]"
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={!canNext}
        >
          {suspiciousCopy.pagination.next}
        </Button>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          className="h-7 px-2 text-[12px]"
          onClick={() => onPageChange(totalPages)}
          disabled={!canNext}
        >
          {suspiciousCopy.pagination.last}
        </Button>
      </div>
    </div>
  );
}
