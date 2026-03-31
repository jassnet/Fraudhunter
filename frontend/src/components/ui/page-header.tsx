import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  meta?: ReactNode;
  actions?: ReactNode;
  status?: ReactNode;
  className?: string;
}

export function PageHeader({ title, meta, actions, status, className }: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex min-h-12 flex-col gap-3 border-b border-border bg-card/40 px-4 py-3 backdrop-blur-sm sm:flex-row sm:flex-wrap sm:items-start sm:justify-between sm:gap-x-4 sm:px-6",
        className
      )}
    >
      <div className="min-w-0 space-y-1">
        <h1 className="text-[1.375rem] font-bold leading-tight tracking-[-0.03em] text-foreground sm:text-[1.75rem]">
          {title}
        </h1>
        {meta ? <div className="text-[13px] text-muted-foreground">{meta}</div> : null}
        {status ? <div className="pt-0.5">{status}</div> : null}
      </div>
      {actions ? (
        <div className="flex w-full min-w-0 flex-col gap-2 sm:w-auto sm:max-w-[min(100%,42rem)] sm:flex-row sm:flex-wrap sm:items-center sm:justify-end">
          {actions}
        </div>
      ) : null}
    </header>
  );
}
