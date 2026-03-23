"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const items = [
  { title: "ダッシュボード", description: "全体傾向の確認", href: "/" },
  { title: "不審クリック", description: "クリック起点の検知一覧", href: "/suspicious/clicks" },
  { title: "不審コンバージョン", description: "CV 起点の検知一覧", href: "/suspicious/conversions" },
];

export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const panelId = "mobile-nav-panel";

  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setOpen(true)}
        aria-expanded={open}
        aria-controls={panelId}
        aria-haspopup="dialog"
        className="rounded"
      >
        メニュー
      </Button>

      {open && (
        <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="ナビゲーション">
          <div className="absolute inset-0 bg-black/50" onClick={() => setOpen(false)} />
          <div id={panelId} className="absolute left-0 top-0 h-full w-[300px] bg-white p-5 shadow-lg">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.32em] text-slate-400">
                  Fraud Checker v2
                </p>
                <span className="mt-2 block text-lg font-semibold tracking-[-0.03em] text-slate-900">
                  不正チェック管理
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setOpen(false)}
                aria-label="ナビゲーションを閉じる"
                className="rounded text-slate-600"
              >
                閉じる
              </Button>
            </div>
            <nav className="mt-6 grid gap-2.5">
              {items.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    aria-current={isActive ? "page" : undefined}
                    className={cn(
                      "rounded border px-4 py-3.5 text-sm transition-colors",
                      isActive
                        ? "border-slate-200 bg-slate-100 text-slate-900"
                        : "border-transparent text-slate-600 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-900"
                    )}
                  >
                    <div className="space-y-1.5">
                      <div className="font-medium">{item.title}</div>
                      <div className="text-xs leading-5 text-slate-400">{item.description}</div>
                    </div>
                  </Link>
                );
              })}
            </nav>
            <div className="absolute bottom-4 left-4 right-4 rounded border border-slate-200 bg-slate-50 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">Notes</p>
              <p className="mt-3 text-xs leading-5 text-slate-500">
                画面は参照専用です。更新系の操作は管理 API または CLI から実行してください。
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
