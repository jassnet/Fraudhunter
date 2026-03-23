import type { ReactNode } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

type MetricTone = "neutral" | "warning" | "danger" | "success";

const toneMap: Record<MetricTone, { label: string; value: string; border: string }> = {
  neutral: {
    label: "text-muted-foreground",
    value: "text-foreground",
    border: "before:bg-border",
  },
  warning: {
    label: "text-[hsl(var(--warning))]",
    value: "text-[hsl(var(--warning))]",
    border: "before:bg-[hsl(var(--warning))]",
  },
  danger: {
    label: "text-destructive",
    value: "text-destructive",
    border: "before:bg-destructive",
  },
  success: {
    label: "text-[hsl(var(--success))]",
    value: "text-[hsl(var(--success))]",
    border: "before:bg-[hsl(var(--success))]",
  },
};

export function MetricStrip({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "grid border border-border bg-card md:grid-cols-2 xl:grid-cols-4",
        className
      )}
    >
      {children}
    </section>
  );
}

interface MetricBlockProps {
  label: string;
  value: ReactNode;
  meta?: ReactNode;
  tone?: MetricTone;
  href?: string;
  ariaLabel?: string;
  valueClassName?: string;
}

export function MetricBlock({
  label,
  value,
  meta,
  tone = "neutral",
  href,
  ariaLabel,
  valueClassName,
}: MetricBlockProps) {
  const toneClasses = toneMap[tone];
  const content = (
    <div
      className={cn(
        "relative flex min-h-[152px] flex-col justify-between border-t border-border p-4 first:border-t-0 md:first:border-t md:odd:border-r xl:border-t-0 xl:border-r xl:last:border-r-0",
        "before:absolute before:left-0 before:top-0 before:h-full before:w-px",
        toneClasses.border
      )}
    >
      <div className="space-y-2">
        <div className={cn("text-[11px] font-semibold uppercase tracking-[0.16em]", toneClasses.label)}>
          {label}
        </div>
        <div className={cn("text-[2.5rem] font-bold tracking-[-0.05em] tabular-nums", toneClasses.value, valueClassName)}>
          {value}
        </div>
      </div>
      {meta ? <div className="text-xs leading-5 text-muted-foreground">{meta}</div> : null}
    </div>
  );

  if (href) {
    return (
      <Link
        href={href}
        aria-label={ariaLabel ?? label}
        className="transition-colors hover:bg-white/[0.02] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white"
      >
        {content}
      </Link>
    );
  }

  return content;
}
