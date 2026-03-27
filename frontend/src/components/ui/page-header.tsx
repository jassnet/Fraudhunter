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
        "flex min-h-12 flex-wrap items-start gap-3 border-b border-border px-6 py-4 sm:px-8",
        className
      )}
    >
      <div className="min-w-0 space-y-1">
        <h1 className="truncate text-[1.75rem] font-bold tracking-[-0.03em] text-foreground">
          {title}
        </h1>
        {meta ? <div className="text-[13px] text-foreground/82">{meta}</div> : null}
        {status ? <div>{status}</div> : null}
      </div>
      {actions ? <div className="ml-auto flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}
