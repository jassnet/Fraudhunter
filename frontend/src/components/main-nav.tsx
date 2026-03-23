"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const items = [
  { title: "ダッシュボード", description: "全体傾向の確認", shortTitle: "集計", href: "/" },
  {
    title: "不審クリック",
    description: "クリック起点の検知一覧",
    shortTitle: "CL",
    href: "/suspicious/clicks",
  },
  {
    title: "不審コンバージョン",
    description: "CV 起点の検知一覧",
    shortTitle: "CV",
    href: "/suspicious/conversions",
  },
];

export function MainNav({ compact = false }: { compact?: boolean }) {
  const pathname = usePathname();

  return (
    <nav className="grid items-start gap-2.5 text-sm font-medium">
      {items.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            aria-label={item.title}
            className={cn(
              "group rounded-lg border transition-all duration-200",
              compact
                ? "flex h-14 items-center justify-center px-2"
                : "px-4 py-3.5",
              isActive
                ? "border-slate-200 bg-slate-100 text-slate-900 shadow-sm"
                : "border-transparent text-slate-600 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-900"
            )}
          >
            {compact ? (
              <span
                className={cn(
                  "text-xs font-semibold uppercase tracking-[0.18em]",
                  isActive ? "text-slate-900" : "text-slate-500"
                )}
              >
                {item.shortTitle}
              </span>
            ) : (
              <div className="space-y-1.5">
                <div
                  className={cn(
                    "text-sm tracking-[-0.01em]",
                    isActive ? "font-semibold text-slate-900" : "font-medium"
                  )}
                >
                  {item.title}
                </div>
                <div className={cn("text-xs leading-5", isActive ? "text-slate-600" : "text-slate-500")}>
                  {item.description}
                </div>
              </div>
            )}
          </Link>
        );
      })}
    </nav>
  );
}
