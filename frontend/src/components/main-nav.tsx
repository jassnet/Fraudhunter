"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const items = [
  { title: "Dashboard", href: "/" },
  { title: "Suspicious Clicks", href: "/suspicious/clicks" },
  { title: "Suspicious Conversions", href: "/suspicious/conversions" },
];

export function MainNav() {
  const pathname = usePathname();

  return (
    <nav className="grid items-start gap-2 text-sm font-medium">
      {items.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "group flex items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:text-primary",
              isActive ? "bg-primary/10 text-primary" : "text-muted-foreground"
            )}
          >
            {item.title}
          </Link>
        );
      })}
    </nav>
  );
}
