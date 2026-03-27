import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type StateTone = "neutral" | "info" | "warning" | "danger";

const toneClasses: Record<StateTone, string> = {
  neutral: "border-border bg-card text-foreground",
  info: "border-[hsl(var(--info))]/45 bg-[hsl(var(--info))]/10 text-foreground",
  warning:
    "border-[hsl(var(--warning))]/45 bg-[hsl(var(--warning))]/10 text-foreground",
  danger: "border-destructive/45 bg-destructive/10 text-foreground",
};

interface StatePanelProps {
  title: string;
  message?: string;
  tone?: StateTone;
  action?: ReactNode;
  eyebrow?: ReactNode;
  className?: string;
}

export function StatePanel({
  title,
  message,
  tone = "neutral",
  action,
  eyebrow,
  className,
}: StatePanelProps) {
  return (
    <section
      className={cn(
        "flex min-h-40 flex-col justify-center gap-3 border px-5 py-5",
        toneClasses[tone],
        className
      )}
    >
      {eyebrow ? <div className="text-[12px] text-foreground/74">{eyebrow}</div> : null}
      <div className="space-y-1">
        <h2 className="text-[15px] font-semibold text-foreground">{title}</h2>
        {message ? <p className="text-[13px] leading-6 text-foreground/80">{message}</p> : null}
      </div>
      {action ? <div className="pt-1">{action}</div> : null}
    </section>
  );
}
