import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title: string;
  message?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ title, message, action, className }: EmptyStateProps) {
  return (
    <div className={cn("flex min-h-48 flex-col items-center justify-center gap-3 border border-border bg-card px-6 text-center", className)}>
      <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-foreground">{title}</h2>
      {message ? <p className="max-w-xl text-sm text-muted-foreground">{message}</p> : null}
      {action}
    </div>
  );
}
