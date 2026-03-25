import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type StatusTone = "high" | "medium" | "low" | "neutral";

const toneClasses: Record<StatusTone, string> = {
  high: "border-destructive bg-destructive/25 text-destructive",
  medium: "border-[hsl(var(--warning))] bg-[hsl(var(--warning))]/25 text-[hsl(var(--warning))]",
  low: "border-[hsl(var(--success))]/85 bg-[hsl(var(--success))]/25 text-[hsl(var(--success))]",
  neutral: "border-border bg-white/[0.07] text-foreground/90",
};

const dotClasses: Record<StatusTone, string> = {
  high: "bg-destructive",
  medium: "bg-[hsl(var(--warning))]",
  low: "bg-[hsl(var(--success))]",
  neutral: "",
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
        "inline-flex min-w-[5.25rem] whitespace-nowrap items-center justify-center gap-1.5 border px-2 py-1 text-xs font-semibold tracking-[0.02em]",
        toneClasses[tone],
        className
      )}
    >
      {tone !== "neutral" && (
        <span
          className={cn("inline-block h-1.5 w-1.5 shrink-0 rounded-full", dotClasses[tone])}
          aria-hidden="true"
        />
      )}
      {children}
    </span>
  );
}
