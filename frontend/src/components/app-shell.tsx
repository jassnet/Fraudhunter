"use client";

import type { ReactNode } from "react";
import { useEffect, useSyncExternalStore, useState } from "react";
import { usePathname } from "next/navigation";
import { MainNav } from "@/components/main-nav";
import { MobileNav } from "@/components/mobile-nav";
import {
  APP_TITLE,
  READ_ONLY_LABEL,
  READ_ONLY_LABEL_COMPACT,
  getPageTitle,
} from "@/components/navigation-config";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ThemeMode = "dark" | "light";

const THEME_STORAGE_KEY = "fc-theme";
const THEME_CHANGE_EVENT = "fc-theme-change";
const DEFAULT_THEME: ThemeMode = "dark";

function readStoredTheme(): ThemeMode {
  if (typeof window === "undefined") return DEFAULT_THEME;
  const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
  return savedTheme === "dark" || savedTheme === "light" ? savedTheme : DEFAULT_THEME;
}

function subscribeTheme(callback: () => void) {
  if (typeof window === "undefined") return () => undefined;
  const handleChange = () => callback();
  window.addEventListener("storage", handleChange);
  window.addEventListener(THEME_CHANGE_EVENT, handleChange);
  return () => {
    window.removeEventListener("storage", handleChange);
    window.removeEventListener(THEME_CHANGE_EVENT, handleChange);
  };
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const theme = useSyncExternalStore(subscribeTheme, readStoredTheme, () => DEFAULT_THEME);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
  }, [theme]);

  const nextThemeAriaLabel =
    theme === "dark" ? "ライトテーマに切り替える" : "ダークテーマに切り替える";
  const themeGlyph = theme === "dark" ? "☀" : "☾";
  const mobilePageTitle = getPageTitle(pathname);
  const toggleTheme = () => {
    const nextTheme = theme === "dark" ? "light" : "dark";
    window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
    window.dispatchEvent(new Event(THEME_CHANGE_EVENT));
  };

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
            sidebarOpen ? "w-[216px]" : "w-16"
          )}
        >
          <div className="flex h-full flex-col">
            <div className="border-b border-border">
              <div className={cn("px-3 pt-3", !sidebarOpen && "sr-only")}>
                <p className="text-[13px] font-semibold leading-snug tracking-tight text-foreground">
                  {APP_TITLE}
                </p>
              </div>
              <div
                className={cn(
                  "flex gap-0.5",
                  sidebarOpen ? "justify-end px-2 pb-2.5 pt-1" : "flex-col items-center px-1 py-2.5",
                )}
              >
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={toggleTheme}
                  aria-label={nextThemeAriaLabel}
                  className="h-8 w-8 text-muted-foreground hover:bg-accent hover:text-foreground"
                >
                  <span className="text-[13px] font-semibold" aria-hidden>
                    {themeGlyph}
                  </span>
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => setSidebarOpen((current) => !current)}
                  aria-label={sidebarOpen ? "サイドバーを閉じる" : "サイドバーを開く"}
                  className="h-8 w-8 text-muted-foreground hover:bg-accent hover:text-foreground"
                >
                  <span className="text-lg leading-none" aria-hidden>
                    {sidebarOpen ? "‹" : "›"}
                  </span>
                </Button>
              </div>
            </div>

            <div className="min-h-0 flex-1 px-2 py-3">
              <MainNav compact={!sidebarOpen} />
            </div>

            <div className="border-t border-border px-3 py-4 text-[11px] text-foreground/68">
              {sidebarOpen ? (
                <div className="space-y-1">
                  <div>{READ_ONLY_LABEL}</div>
                  <div className="text-[10px] text-foreground/48">v2.0.0</div>
                </div>
              ) : (
                <div className="text-center text-[10px]">{READ_ONLY_LABEL_COMPACT}</div>
              )}
            </div>
          </div>
        </aside>

        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <header className="flex h-12 items-center gap-3 border-b border-border bg-card px-4 md:hidden">
            <MobileNav />
            <div className="min-w-0 flex-1 truncate text-sm font-semibold text-foreground">
              {mobilePageTitle}
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              aria-label={nextThemeAriaLabel}
              className="h-8 w-8 shrink-0 text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <span className="text-[13px] font-semibold" aria-hidden>
                {themeGlyph}
              </span>
            </Button>
          </header>

          <main
            id="main-content"
            className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden"
          >
            {children}
          </main>
        </div>
      </div>
    </>
  );
}
