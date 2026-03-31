"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/components/navigation-config";
import { cn } from "@/lib/utils";

export function MainNav({ compact = false }: { compact?: boolean }) {
  const pathname = usePathname();

  return (
    <nav className="grid gap-1.5">
      {NAV_ITEMS.map((item) => {
        const isActive =
          item.href === "/" ? pathname === item.href : pathname?.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            aria-label={item.title}
            className={cn(
              "relative flex rounded-[var(--radius)] border-l-2 border-transparent px-3 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              compact ? "h-12 items-center justify-center" : "h-11 items-center",
              isActive
                ? "border-foreground bg-foreground/[0.06] text-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            <span className={cn(compact ? "text-xs font-semibold" : "font-medium")}>
              {compact ? item.shortTitle : item.title}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
