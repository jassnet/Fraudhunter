"use client";

import { Button } from "@/components/ui/button";

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
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-3 text-[13px] text-foreground/78">
      <div aria-label="件数範囲" aria-live="polite">
        {resultRange}
      </div>
      <div className="flex items-center gap-2">
        <Button size="sm" variant="outline" onClick={() => onPageChange(1)} disabled={!canPrev}>
          最初
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={!canPrev}
        >
          前へ
        </Button>
        <span className="tabular-nums text-foreground/86">
          {page} / {totalPages}
        </span>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={!canNext}
        >
          次へ
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onPageChange(totalPages)}
          disabled={!canNext}
        >
          最後
        </Button>
      </div>
    </div>
  );
}
