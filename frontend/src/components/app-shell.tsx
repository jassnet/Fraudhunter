"use client";

import { useState } from "react";
import { MainNav } from "@/components/main-nav";
import { MobileNav } from "@/components/mobile-nav";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-background focus:px-3 focus:py-2 focus:text-sm focus:shadow"
      >
        メインコンテンツへ移動
      </a>

      <div className="flex h-dvh overflow-hidden bg-background">
        <aside
          className={cn(
            "hidden shrink-0 overflow-hidden border-r border-slate-200 bg-white transition-[width] duration-200 md:block",
            sidebarOpen ? "w-[18rem]" : "w-[5.5rem]"
          )}
        >
          <div className="flex h-full flex-col">
            <div className="border-b border-slate-200 px-4 py-5">
              <div className="flex items-start justify-between gap-3">
                <div className={cn("min-w-0", !sidebarOpen && "sr-only")}>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.32em] text-slate-400">
                    Fraud Checker v2
                  </p>
                  <div className="mt-3 space-y-1.5">
                    <span className="block text-xl font-semibold tracking-[-0.03em] text-slate-900">
                      不正チェック管理
                    </span>
                    <p className="max-w-[14rem] text-sm leading-6 text-slate-500">
                      日次の流入監視と不審傾向の確認。
                    </p>
                  </div>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setSidebarOpen((current) => !current)}
                  aria-label={sidebarOpen ? "サイドバーを閉じる" : "サイドバーを開く"}
                  className="h-9 w-9 shrink-0 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-100"
                >
                  {sidebarOpen ? "←" : "→"}
                </Button>
              </div>
            </div>

            <div className="flex-1 px-3 py-4">
              <MainNav compact={!sidebarOpen} />
            </div>

            <div className="mt-auto border-t border-slate-200 p-4">
              <div
                className={cn(
                  "rounded-lg border border-slate-200 bg-slate-50 p-4",
                  !sidebarOpen && "px-3 py-4"
                )}
              >
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                  Notes
                </p>
                {sidebarOpen ? (
                  <>
                    <p className="mt-3 text-xs leading-5 text-slate-500">
                      画面は参照専用です。取込や更新ジョブは管理 API または CLI から実行してください。
                    </p>
                    <div className="mt-3 flex items-center justify-between">
                      <span className="text-[11px] uppercase tracking-[0.2em] text-slate-400">v2.0.0</span>
                    </div>
                  </>
                ) : (
                  <div className="mt-3 text-center text-[11px] uppercase tracking-[0.2em] text-slate-400">v2</div>
                )}
              </div>
            </div>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-14 items-center gap-4 border-b border-slate-200 bg-white px-4 md:hidden">
            <MobileNav />
            <span className="font-semibold">不正チェック管理</span>
          </header>

          <main id="main-content" className="min-w-0 flex-1 overflow-auto">
            {children}
          </main>
        </div>
      </div>
    </>
  );
}
