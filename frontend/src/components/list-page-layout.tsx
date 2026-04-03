"use client";

import type { ReactNode } from "react";
import { PageHeader } from "@/components/ui/page-header";

interface ListPageLayoutProps {
  actions?: ReactNode;
  children: ReactNode;
  meta?: ReactNode;
  searchBar?: ReactNode;
  sidePanel?: ReactNode;
  status?: ReactNode;
  title: string;
}

export function ListPageLayout({
  actions,
  children,
  meta,
  searchBar,
  sidePanel,
  status,
  title,
}: ListPageLayoutProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <PageHeader
        className="shrink-0"
        title={title}
        meta={meta}
        status={status}
        actions={actions}
      />

      {searchBar}

      {sidePanel ? (
        <div className="flex min-h-0 flex-1 overflow-hidden">
          {children}
          {sidePanel}
        </div>
      ) : (
        children
      )}
    </div>
  );
}
