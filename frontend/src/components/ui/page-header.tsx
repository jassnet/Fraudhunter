import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  meta?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function PageHeader({ title, meta, actions, className }: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex min-h-12 flex-wrap items-center gap-3 border-b border-border px-6 py-4 sm:px-8",
        className
      )}
    >
      <div className="flex min-w-0 items-baseline gap-3">
        <h1 className="truncate text-[1.75rem] font-bold tracking-[-0.04em] text-foreground">
          {title}
        </h1>
        {meta ? <span className="truncate text-xs text-muted-foreground">{meta}</span> : null}
      </div>
      {actions ? <div className="ml-auto flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}
