"use client";

import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

import Link from "next/link";
import { usePathname } from "next/navigation";

function resolveActive(pathname: string, href: string) {
  if (href === "/alerts") {
    return pathname === href || pathname.startsWith("/alerts/");
  }
  return pathname === href;
}

function DashboardIcon() {
  return (
    <svg className="sidebar__link-icon" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <rect x="1" y="9" width="4" height="8" rx="1" fill="currentColor" opacity="0.6" />
      <rect x="7" y="5" width="4" height="12" rx="1" fill="currentColor" opacity="0.85" />
      <rect x="13" y="1" width="4" height="16" rx="1" fill="currentColor" />
    </svg>
  );
}

function AlertsIcon() {
  return (
    <svg className="sidebar__link-icon" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <path
        d="M9 1.5L2 14h14L9 1.5z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
        fill="none"
      />
      <rect x="8.25" y="7" width="1.5" height="4" rx="0.75" fill="currentColor" />
      <circle cx="9" cy="12.5" r="0.75" fill="currentColor" />
    </svg>
  );
}

function AlgorithmIcon() {
  return (
    <svg className="sidebar__link-icon" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <circle cx="9" cy="4" r="2.5" stroke="currentColor" strokeWidth="1.3" />
      <circle cx="4" cy="14" r="2.5" stroke="currentColor" strokeWidth="1.3" />
      <circle cx="14" cy="14" r="2.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M9 6.5V9M9 9L5.5 11.5M9 9L12.5 11.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

function ChevronLeftIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChevronRightIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M6 3l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

const NAV_ITEMS = [
  { href: "/dashboard", label: "ダッシュボード", Icon: DashboardIcon },
  { href: "/alerts", label: "アラート一覧", Icon: AlertsIcon },
  { href: "/algorithm", label: "検知アルゴリズム", Icon: AlgorithmIcon },
] as const;

export function AppFrame({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const sidebarRef = useRef<HTMLElement | null>(null);
  const mobileCloseButtonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (!mobileOpen) {
      document.body.style.removeProperty("overflow");
      return undefined;
    }

    document.body.style.setProperty("overflow", "hidden");
    mobileCloseButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMobileOpen(false);
        return;
      }
      if (event.key !== "Tab" || !sidebarRef.current) {
        return;
      }

      const focusable = sidebarRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
      );
      if (focusable.length === 0) {
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;

      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.removeProperty("overflow");
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [mobileOpen]);

  return (
    <div className={`app-shell${collapsed ? " sidebar-collapsed" : ""}`}>
      {/* モバイル用トップバー */}
      <div className="mobile-topbar">
        <button
          className="mobile-topbar-btn"
          onClick={() => setMobileOpen(true)}
          aria-label="メニューを開く"
        >
          <MenuIcon />
        </button>
        <span>フロードチェッカー</span>
      </div>

      {/* オーバーレイ背景 */}
      {mobileOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* サイドバー */}
      <aside
        ref={sidebarRef}
        className={`sidebar${collapsed ? " sidebar--collapsed" : ""}${mobileOpen ? " sidebar--open" : ""}`}
        aria-label="主要ナビゲーション"
        aria-modal={mobileOpen ? "true" : undefined}
        role={mobileOpen ? "dialog" : undefined}
      >
        <div className="sidebar__brand">
          <div className="sidebar__brand-icon">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M8 1L2 5v4c0 3.3 2.6 6.2 6 7 3.4-.8 6-3.7 6-7V5L8 1z" stroke="#fff" strokeWidth="1.4" fill="none" />
              <path d="M5.5 8.5l2 2 3.5-4" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <span className="sidebar__brand-text">フロードチェッカー</span>
          <button
            ref={mobileCloseButtonRef}
            className="sidebar__mobile-close"
            type="button"
            onClick={() => setMobileOpen(false)}
            aria-label="メニューを閉じる"
          >
            <ChevronLeftIcon />
          </button>
        </div>

        <nav className="sidebar__nav">
          {NAV_ITEMS.map(({ href, label, Icon }) => (
            <Link
              key={href}
              className={`sidebar__link${resolveActive(pathname, href) ? " sidebar__link--active" : ""}`}
              href={href}
              title={collapsed ? label : undefined}
              onClick={() => setMobileOpen(false)}
            >
              <Icon />
              <span className="sidebar__link-label">{label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar__footer">
          <button
            className="sidebar__toggle"
            onClick={() => setCollapsed((c) => !c)}
            aria-label={collapsed ? "サイドバーを展開" : "サイドバーを折り畳む"}
          >
            {collapsed ? <ChevronRightIcon /> : <ChevronLeftIcon />}
          </button>
        </div>
      </aside>

      <main className="console-main">{children}</main>
    </div>
  );
}
