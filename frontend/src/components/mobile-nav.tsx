"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const items = [
  { title: "Dashboard", href: "/" },
  { title: "Suspicious Clicks", href: "/suspicious/clicks" },
  { title: "Suspicious Conversions", href: "/suspicious/conversions" },
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
      >
        Menu
      </Button>

      {open && (
        <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Navigation">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setOpen(false)}
          />
          <div
            id={panelId}
            className="absolute left-0 top-0 h-full w-[280px] bg-background p-4 shadow-lg"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold">Fraud Checker v2</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setOpen(false)}
                aria-label="Close navigation"
              >
                Close
              </Button>
            </div>
            <nav className="mt-6 grid gap-2">
              {items.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    aria-current={isActive ? "page" : undefined}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-muted hover:text-primary"
                    )}
                  >
                    {item.title}
                  </Link>
                );
              })}
            </nav>
            <div className="absolute bottom-4 left-4 right-4">
              <p className="text-xs text-muted-foreground">v2.0.0</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
