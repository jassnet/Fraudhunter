"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";

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
] as const;

export function AppFrame({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("sidebar-collapsed");
      if (stored === "true") setCollapsed(true);
    } catch {
      // localStorage利用不可の場合は無視
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem("sidebar-collapsed", String(collapsed));
    } catch {
      // localStorage利用不可の場合は無視
    }
  }, [collapsed]);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

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
        <span>Fraud Checker</span>
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
        className={`sidebar${collapsed ? " sidebar--collapsed" : ""}${mobileOpen ? " sidebar--open" : ""}`}
        aria-label="主要ナビゲーション"
      >
        <div className="sidebar__brand">
          <div className="sidebar__brand-icon">FC</div>
          <span className="sidebar__brand-text">Fraud Checker</span>
        </div>

        <nav className="sidebar__nav">
          {NAV_ITEMS.map(({ href, label, Icon }) => (
            <Link
              key={href}
              className={`sidebar__link${resolveActive(pathname, href) ? " sidebar__link--active" : ""}`}
              href={href}
              title={collapsed ? label : undefined}
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
