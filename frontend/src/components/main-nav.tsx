"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  ShieldAlert,
  MousePointerClick,
  Target,
  Settings
} from "lucide-react";

const items = [
  {
    title: "ダッシュボード",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    title: "不正クリック検知",
    href: "/suspicious/clicks",
    icon: MousePointerClick,
  },
  {
    title: "不正成果検知",
    href: "/suspicious/conversions",
    icon: Target,
  },
  {
    title: "設定",
    href: "/settings",
    icon: Settings,
  },
];

export function MainNav() {
  const pathname = usePathname();

  return (
    <nav className="grid items-start gap-2 text-sm font-medium">
      {items.map((item, index) => {
        const Icon = item.icon;
        return (
          <Link
            key={index}
            href={item.href}
            className={cn(
              "group flex items-center gap-3 rounded-lg px-3 py-2 transition-all hover:text-primary",
              pathname === item.href
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground"
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

