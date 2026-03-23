import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function ControlBar({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-3 border border-border bg-card px-4 py-3",
        className
      )}
    >
      {children}
    </div>
  );
}
