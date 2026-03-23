"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const items = [
  { title: "ダッシュボード", description: "全体傾向の確認", href: "/" },
  { title: "不審クリック", description: "クリック起点の検知一覧", href: "/suspicious/clicks" },
  { title: "不審コンバージョン", description: "CV 起点の検知一覧", href: "/suspicious/conversions" },
];

export function MainNav() {
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
            className={cn(
              "group rounded-lg border px-4 py-3.5 transition-all duration-200",
              isActive
                ? "border-slate-200 bg-slate-100 text-slate-900 shadow-sm"
                : "border-transparent text-slate-600 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-900"
            )}
          >
            <div className="space-y-1.5">
              <div className={cn("text-sm tracking-[-0.01em]", isActive ? "font-semibold text-slate-900" : "font-medium")}>
                {item.title}
              </div>
              <div className={cn("text-xs leading-5", isActive ? "text-slate-600" : "text-slate-500")}>
                {item.description}
              </div>
            </div>
          </Link>
        );
      })}
    </nav>
  );
}
