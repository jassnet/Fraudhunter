"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, MousePointerClick, Target, Settings } from "lucide-react";

const items = [
  { title: "ダッシュボード", href: "/", icon: LayoutDashboard },
  { title: "不正クリック検知", href: "/suspicious/clicks", icon: MousePointerClick },
  { title: "不正成果検知", href: "/suspicious/conversions", icon: Target },
  { title: "設定", href: "/settings", icon: Settings },
];

export function MainNav() {
  const pathname = usePathname();

  return (
    <nav className="grid items-start gap-2 text-sm font-medium">
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "group flex items-center gap-3 rounded-lg px-3 py-2 transition-all hover:text-primary",
              isActive ? "bg-primary/10 text-primary" : "text-muted-foreground"
            )}
          >
            <Icon className="h-4 w-4" />
            {item.title}
          </Link>
        );
      })}
    </nav>
  );
}
