"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const items = [
  { title: "ダッシュボード", shortTitle: "DB", href: "/" },
  { title: "不審クリック", shortTitle: "CL", href: "/suspicious/clicks" },
  { title: "不審コンバージョン", shortTitle: "CV", href: "/suspicious/conversions" },
];

export function MainNav({ compact = false }: { compact?: boolean }) {
  const pathname = usePathname();

  return (
    <nav className="grid gap-1.5">
      {items.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            aria-label={item.title}
            className={cn(
              "relative flex border-l border-transparent px-3 text-sm transition-colors",
              compact ? "h-12 items-center justify-center" : "h-11 items-center",
              isActive
                ? "border-foreground bg-foreground/[0.04] text-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            <span
              className={cn(
                compact ? "text-xs font-semibold uppercase tracking-[0.16em]" : "font-medium"
              )}
            >
              {compact ? item.shortTitle : item.title}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
