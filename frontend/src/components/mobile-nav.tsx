"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const items = [
  { title: "ダッシュボード", href: "/" },
  { title: "不審クリック", href: "/suspicious/clicks" },
  { title: "不審コンバージョン", href: "/suspicious/conversions" },
];

export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

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
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => setOpen(true)}
        aria-expanded={open}
        aria-controls="mobile-nav-panel"
        aria-haspopup="dialog"
        className="border border-border text-xs"
      >
        Menu
      </Button>

      {open ? (
        <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true" aria-label="ナビゲーション">
          <div className="absolute inset-0 bg-black/70" onClick={() => setOpen(false)} />
          <div
            id="mobile-nav-panel"
            className="absolute left-0 top-0 flex h-full w-[280px] flex-col border-r border-border bg-card"
          >
            <div className="flex items-center justify-between border-b border-border p-4">
              <div className="text-sm font-semibold text-foreground">Monitoring</div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setOpen(false)}
                aria-label="ナビゲーションを閉じる"
                className="text-xs"
              >
                Close
              </Button>
            </div>
            <nav className="grid gap-1.5 p-3">
              {items.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    aria-current={isActive ? "page" : undefined}
                    className={cn(
                      "flex h-11 items-center border-l px-3 text-sm",
                      isActive
                        ? "border-foreground bg-foreground/[0.04] text-foreground"
                        : "border-transparent text-muted-foreground hover:bg-accent hover:text-foreground"
                    )}
                  >
                    {item.title}
                  </Link>
                );
              })}
            </nav>
            <div className="mt-auto border-t border-border p-4 text-[11px] text-muted-foreground">
              Read Only
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
