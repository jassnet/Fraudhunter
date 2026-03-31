"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { APP_TITLE, NAV_ITEMS, READ_ONLY_LABEL } from "@/components/navigation-config";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    const previousOverflow = document.body.style.overflow;
    const previousTouchAction = document.body.style.touchAction;
    document.body.style.overflow = "hidden";
    document.body.style.touchAction = "none";
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.body.style.touchAction = previousTouchAction;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => setOpen(true)}
        aria-expanded={open}
        aria-controls="mobile-nav-panel"
        aria-haspopup="dialog"
        className="border border-border text-xs"
      >
        メニュー
      </Button>

      {open ? (
        <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true" aria-label="ナビゲーション">
          <div
            className="fc-mobile-nav-backdrop absolute inset-0 transition-opacity"
            onClick={() => setOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 w-[min(86vw,296px)] bg-transparent">
            <div
              id="mobile-nav-panel"
              className="fc-mobile-nav-panel flex h-full flex-col"
            >
              <div className="flex items-center justify-between border-b border-border/80 px-4 py-4">
                <div className="space-y-0.5">
                  <div className="text-sm font-semibold text-foreground">{APP_TITLE}</div>
                  <div className="text-[11px] text-muted-foreground">画面を切り替え</div>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setOpen(false)}
                  aria-label="ナビゲーションを閉じる"
                  className="text-xs"
                >
                  閉じる
                </Button>
              </div>
              <nav className="grid gap-1.5 p-3">
                {NAV_ITEMS.map((item) => {
                  const isActive =
                    item.href === "/" ? pathname === item.href : pathname?.startsWith(item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setOpen(false)}
                      aria-current={isActive ? "page" : undefined}
                      className={cn(
                        "flex h-11 items-center rounded-[var(--radius)] border-l-2 border-transparent px-3 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        isActive
                          ? "border-foreground bg-foreground/[0.08] text-foreground shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)]"
                          : "text-muted-foreground hover:bg-accent hover:text-foreground"
                      )}
                    >
                      {item.title}
                    </Link>
                  );
                })}
              </nav>
              <div className="mt-auto border-t border-border/80 px-4 py-4">
                <div className="text-[11px] text-muted-foreground">{READ_ONLY_LABEL}</div>
                <div className="mt-1 text-[10px] text-foreground/48">外側をタップして閉じられます</div>
              </div>
            </div>
            <div
              aria-hidden
              className="fc-mobile-nav-edge pointer-events-none absolute inset-y-0 left-full w-10"
            />
          </div>
        </div>
      ) : null}
    </>
  );
}
