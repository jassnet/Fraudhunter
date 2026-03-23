import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type StatusTone = "high" | "medium" | "low" | "neutral";

const toneClasses: Record<StatusTone, string> = {
  high: "border-destructive/60 bg-destructive/10 text-destructive",
  medium: "border-[hsl(var(--warning))]/70 bg-[hsl(var(--warning))]/10 text-[hsl(var(--warning))]",
  low: "border-[hsl(var(--success))]/60 bg-[hsl(var(--success))]/10 text-[hsl(var(--success))]",
  neutral: "border-border bg-muted text-muted-foreground",
};

export function StatusBadge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: StatusTone;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex min-w-16 items-center justify-center border px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.12em]",
        toneClasses[tone],
        className
      )}
    >
      {children}
    </span>
  );
}
