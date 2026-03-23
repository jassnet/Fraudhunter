import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SectionFrameProps {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}

export function SectionFrame({
  title,
  actions,
  children,
  className,
  bodyClassName,
}: SectionFrameProps) {
  return (
    <section className={cn("border border-border bg-card", className)}>
      {title || actions ? (
        <div className="flex min-h-11 items-center justify-between gap-3 border-b border-border px-4 py-3">
          <h2 className="text-sm font-semibold uppercase tracking-[0.12em] text-foreground">{title}</h2>
          {actions}
        </div>
      ) : null}
      <div className={cn("p-4", bodyClassName)}>{children}</div>
    </section>
  );
}
