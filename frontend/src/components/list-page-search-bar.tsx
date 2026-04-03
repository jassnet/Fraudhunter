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
        "fc-search-strip shrink-0 px-3 py-2.5 sm:px-4",
        className
      )}
    >
      {children}
    </div>
  );
}
