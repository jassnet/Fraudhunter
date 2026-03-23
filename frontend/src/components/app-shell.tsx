"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { MainNav } from "@/components/main-nav";
import { MobileNav } from "@/components/mobile-nav";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ThemeMode = "dark" | "light";

const THEME_STORAGE_KEY = "fc-theme";

export function AppShell({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [theme, setTheme] = useState<ThemeMode>("dark");

  useEffect(() => {
    const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (savedTheme === "dark" || savedTheme === "light") {
      setTheme(savedTheme);
    }
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  };

  const nextThemeLabel = theme === "dark" ? "LIGHT" : "DARK";
  const nextThemeAriaLabel =
    theme === "dark" ? "ライトテーマに切り替える" : "ダークテーマに切り替える";

  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:border focus:border-foreground focus:bg-card focus:px-3 focus:py-2 focus:text-sm"
      >
        メインコンテンツへ移動
      </a>

      <div className="flex h-dvh overflow-hidden bg-background text-foreground">
        <aside
          className={cn(
            "hidden shrink-0 overflow-hidden border-r border-border bg-card transition-[width] duration-200 md:block",
            sidebarOpen ? "w-[240px]" : "w-16"
          )}
        >
          <div className="flex h-full flex-col">
            <div className="border-b border-border p-4">
              <div className="flex items-start justify-between gap-2">
                <div className={cn("min-w-0", !sidebarOpen && "sr-only")}>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.24em] text-muted-foreground">
                    Fraud Checker
                  </div>
                  <div className="mt-3 text-lg font-semibold tracking-[-0.04em] text-foreground">
                    Dashboard
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={toggleTheme}
                    aria-label={nextThemeAriaLabel}
                    className={cn(
                      "h-8 border border-border px-2 text-[10px] font-semibold uppercase tracking-[0.14em]",
                      !sidebarOpen && "w-8 px-0"
                    )}
                  >
                    {sidebarOpen ? nextThemeLabel : nextThemeLabel.slice(0, 1)}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => setSidebarOpen((current) => !current)}
                    aria-label={sidebarOpen ? "サイドバーを閉じる" : "サイドバーを開く"}
                    className="h-8 w-8 border border-border text-muted-foreground hover:bg-accent hover:text-foreground"
                  >
                    {sidebarOpen ? "−" : "+"}
                  </Button>
                </div>
              </div>
            </div>

            <div className="min-h-0 flex-1 px-2 py-3">
              <MainNav compact={!sidebarOpen} />
            </div>

            <div className="border-t border-border px-3 py-4 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              {sidebarOpen ? (
                <div className="space-y-2">
                  <div>Read Only</div>
                  <div className="text-[10px] text-muted-foreground/70">v2.0.0</div>
                </div>
              ) : (
                <div className="text-center">RO</div>
              )}
            </div>
          </div>
        </aside>

        <div className="flex min-w-0 min-h-0 flex-1 flex-col">
          <header className="flex h-12 items-center gap-3 border-b border-border bg-card px-4 md:hidden">
            <MobileNav />
            <div className="min-w-0 flex-1 truncate text-sm font-semibold uppercase tracking-[0.18em] text-foreground">
              Dashboard
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              aria-label={nextThemeAriaLabel}
              className="h-8 border border-border px-2 text-[10px] font-semibold uppercase tracking-[0.14em]"
            >
              {nextThemeLabel}
            </Button>
          </header>

          <main id="main-content" className="min-w-0 min-h-0 flex-1 overflow-hidden">
            {children}
          </main>
        </div>
      </div>
    </>
  );
}
