import type { Metadata } from "next";
import "./globals.css";
import { MainNav } from "@/components/main-nav";
import { MobileNav } from "@/components/mobile-nav";

export const metadata: Metadata = {
  title: "Fraud Checker v2",
  description: "不正検知ダッシュボード",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body suppressHydrationWarning>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-background focus:px-3 focus:py-2 focus:text-sm focus:shadow"
        >
          メインコンテンツへ移動
        </a>
        <div className="flex h-dvh overflow-auto bg-background">
          <aside className="hidden w-72 overflow-y-auto border-r border-slate-200 bg-white md:block">
            <div className="flex h-full flex-col gap-2">
              <div className="border-b border-slate-200 px-6 py-7">
                <p className="text-[10px] font-semibold uppercase tracking-[0.32em] text-slate-400">
                  Fraud Checker v2
                </p>
                <div className="mt-4 space-y-2">
                  <span className="block text-xl font-semibold tracking-[-0.03em] text-slate-900">
                    不正チェック管理
                  </span>
                  <p className="max-w-[13rem] text-sm leading-6 text-slate-500">
                    日次の流入監視と不審傾向の確認。
                  </p>
                </div>
              </div>
              <div className="flex-1 px-4 py-4">
                <MainNav />
              </div>
              <div className="mt-auto border-t border-slate-200 p-4">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                    Notes
                  </p>
                  <p className="mt-3 text-xs leading-5 text-slate-500">
                    画面は参照専用です。取込や更新ジョブは管理 API または CLI から実行してください。
                  </p>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-[11px] uppercase tracking-[0.2em] text-slate-400">v2.0.0</span>
                  </div>
                </div>
              </div>
            </div>
          </aside>

          <div className="flex flex-1 flex-col">
            <header className="flex h-14 items-center gap-4 border-b border-slate-200 bg-white px-4 md:hidden">
              <MobileNav />
              <span className="font-semibold">不正チェック管理</span>
            </header>

            <main id="main-content" className="flex-1 overflow-auto">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
