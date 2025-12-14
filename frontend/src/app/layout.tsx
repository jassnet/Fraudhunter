import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { MainNav } from "@/components/main-nav";
import { ModeToggle } from "@/components/mode-toggle";
import { MobileNav } from "@/components/mobile-nav";
import { JobStatusIndicator } from "@/components/job-status-indicator";
import { SetupWarning } from "@/components/setup-warning";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Fraud Checker v2",
  description: "Advanced Fraud Detection System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <div className="flex h-screen overflow-auto bg-background">
            {/* デスクトップサイドバー */}
            <aside className="hidden w-64 overflow-y-auto border-r bg-muted/40 md:block">
              <div className="flex h-full flex-col gap-2">
                <div className="flex h-14 items-center border-b px-6 font-semibold lg:h-[60px]">
                  <span className="">Fraud Checker v2</span>
                </div>
                <div className="flex-1 px-4 py-4">
                  <MainNav />
                </div>
                <div className="mt-auto p-4 border-t space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">ジョブ状態</span>
                    <JobStatusIndicator />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">v2.0.0</span>
                    <ModeToggle />
                  </div>
                </div>
              </div>
            </aside>
            
            {/* モバイルヘッダー + メインコンテンツ */}
            <div className="flex flex-1 flex-col">
              {/* モバイルヘッダー */}
              <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-4 md:hidden">
                <MobileNav />
                <span className="font-semibold">Fraud Checker v2</span>
                <div className="ml-auto">
                  <div className="flex items-center gap-3">
                    <JobStatusIndicator />
                    <ModeToggle />
                  </div>
                </div>
              </header>
              
              {/* セットアップ警告 */}
              <SetupWarning />
              
              {/* メインコンテンツ */}
              <main className="flex-1 overflow-auto">
                {children}
              </main>
            </div>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
