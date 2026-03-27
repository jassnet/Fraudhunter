import type { ReactNode } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

type MetricTone = "neutral" | "warning" | "danger" | "success";
export type MetricEmphasis = "primary" | "alert" | "diagnostic";

const toneMap: Record<MetricTone, { label: string; value: string; border: string }> = {
  neutral: {
    label: "text-foreground/82",
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
  emphasis?: MetricEmphasis;
  href?: string;
  ariaLabel?: string;
  valueClassName?: string;
}

export function MetricBlock({
  label,
  value,
  meta,
  tone = "neutral",
  emphasis = "primary",
  href,
  ariaLabel,
  valueClassName,
}: MetricBlockProps) {
  const toneClasses = toneMap[tone];
  const emphasisClasses =
    emphasis === "diagnostic"
      ? {
          label: "text-[11px] text-foreground/78",
          value: "text-[1.85rem] text-foreground",
          meta: "text-[12px] leading-5 text-foreground/72",
        }
      : emphasis === "alert"
        ? {
            label: "text-[12px]",
            value: "text-[2.8rem]",
            meta: "text-[13px] leading-5 text-foreground/82",
          }
        : {
            label: "text-[12px]",
            value: "text-[2.65rem]",
            meta: "text-[13px] leading-5 text-foreground/80",
          };

  const content = (
    <div
      className={cn(
        "relative flex min-h-[152px] flex-col justify-between border-t border-border p-4 first:border-t-0 md:first:border-t md:odd:border-r xl:border-t-0 xl:border-r xl:last:border-r-0",
        "before:absolute before:left-0 before:top-0 before:h-full before:w-px",
        toneClasses.border
      )}
    >
      <div className="space-y-2">
        <div
          className={cn(
            "font-semibold tracking-[0.02em]",
            toneClasses.label,
            emphasisClasses.label
          )}
        >
          {label}
        </div>
        <div
          className={cn(
            "font-bold tracking-[-0.04em] tabular-nums",
            toneClasses.value,
            emphasisClasses.value,
            valueClassName
          )}
        >
          {value}
        </div>
      </div>
      {meta ? <div className={emphasisClasses.meta}>{meta}</div> : null}
    </div>
  );

  if (href) {
    return (
      <Link
        href={href}
        aria-label={ariaLabel ?? label}
        className="transition-colors hover:bg-white/[0.07] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white"
      >
        {content}
      </Link>
    );
  }

  return content;
}
