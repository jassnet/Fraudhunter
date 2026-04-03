"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function ListPageSearchBar({
  children,
  className,
  id,
}: {
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <div
      id={id}
      className={cn(
        "shrink-0 border-b border-border bg-muted/20 px-3 py-2.5 sm:px-4",
        className
      )}
    >
      {children}
    </div>
  );
}
