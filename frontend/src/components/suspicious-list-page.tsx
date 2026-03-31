"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { SuspiciousListControls } from "@/components/suspicious-list-controls";
import { SuspiciousListPagination } from "@/components/suspicious-list-pagination";
import { SuspiciousListTable } from "@/components/suspicious-list-table";
import { SuspiciousRowDetails } from "@/components/suspicious-row-details";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/ui/state-panel";
import { dashboardCopy } from "@/copy/dashboard";
import { suspiciousCopy } from "@/copy/suspicious";
import { useSuspiciousData } from "@/features/suspicious-list/use-suspicious-data";
import { useSuspiciousDetails } from "@/features/suspicious-list/use-suspicious-details";
import {
  type SuspiciousSortValue,
  useSuspiciousListUrlState,
} from "@/features/suspicious-list/url-state";
import type { SuspiciousItem, SuspiciousQueryOptions, SuspiciousResponse } from "@/lib/api";
import type { MetricKey } from "@/features/suspicious-list/suspicious-list-table-config";

const GROUP_BY_REASON_STORAGE_KEY = "suspicious:list:group-by-reason";
type SuspiciousFetcher = (
  date?: string,
  limit?: number,
  offset?: number,
  options?: SuspiciousQueryOptions
) => Promise<SuspiciousResponse>;
type SuspiciousDetailFetcher = (findingKey: string) => Promise<SuspiciousItem>;

interface SuspiciousListPageProps {
  title: string;
  countLabel: string;
  fetcher: SuspiciousFetcher;
  fetchDetail: SuspiciousDetailFetcher;
  metricKey: MetricKey;
}

export default function SuspiciousListPage({
  title,
  countLabel,
  fetcher,
  fetchDetail,
  metricKey,
}: SuspiciousListPageProps) {
  const { state, setDate, setPage, setRisk, setSearch, setSort } = useSuspiciousListUrlState();
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [groupByReason, setGroupByReason] = useState(() => {
    try {
      return localStorage.getItem(GROUP_BY_REASON_STORAGE_KEY) === "1";
    } catch {
      return false;
    }
  });
  const [searchDraft, setSearchDraft] = useState(() => state.search);
  const [searchPanelOpen, setSearchPanelOpen] = useState(() => state.search.trim().length > 0);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!searchPanelOpen) return;
    const id = requestAnimationFrame(() => searchInputRef.current?.focus());
    return () => cancelAnimationFrame(id);
  }, [searchPanelOpen]);

  useEffect(() => {
    const handle = setTimeout(() => {
      if (searchDraft !== state.search) {
        setSearch(searchDraft);
      }
    }, 300);
    return () => clearTimeout(handle);
  }, [searchDraft, setSearch, state.search]);

  const {
    data,
    totalPages,
    availableDates,
    status,
    message,
    lastUpdated,
    resultRange,
    isRefreshing,
    reload,
  } = useSuspiciousData({
    fetcher,
    date: state.date,
    page: state.page,
    search: state.search,
    risk: state.risk,
    sort: state.sort,
    sortOrder: state.sortOrder,
  });

  useEffect(() => {
    if (!state.date && availableDates[0]) {
      setDate(availableDates[0]);
    }
  }, [availableDates, setDate, state.date]);

  useEffect(() => {
    try {
      localStorage.setItem(GROUP_BY_REASON_STORAGE_KEY, groupByReason ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, [groupByReason]);

  const { loadDetail, getDetailState } = useSuspiciousDetails(fetchDetail);

  const resolvedExpandedRow = useMemo(() => {
    if (!expandedRow) return null;
    return data.some((item) => (item.finding_key || `${item.ipaddress}-${item.useragent}`) === expandedRow)
      ? expandedRow
      : null;
  }, [data, expandedRow]);

  const detailPanelState = useMemo(() => {
    if (!resolvedExpandedRow) return null;
    const item = data.find(
      (row) => (row.finding_key || `${row.ipaddress}-${row.useragent}`) === resolvedExpandedRow
    );
    if (!item) return null;
    return getDetailState(item);
  }, [data, getDetailState, resolvedExpandedRow]);

  const drawerOpen = Boolean(detailPanelState);

  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setExpandedRow(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerOpen]);

  const pageStatus =
    status === "unauthorized" ? (
      <span className="text-[12px] text-[hsl(var(--warning))]">{suspiciousCopy.states.unauthorizedTitle}</span>
    ) : status === "forbidden" ? (
      <span className="text-[12px] text-destructive">{suspiciousCopy.states.forbiddenTitle}</span>
    ) : null;

  const handleOpenDetail = async (item: SuspiciousItem) => {
    const rowKey = item.finding_key || `${item.ipaddress}-${item.useragent}`;
    setExpandedRow(rowKey);
    await loadDetail(item);
  };

  const closeDetail = () => setExpandedRow(null);

  const renderBody = () => {
    if (status === "loading" || status === "refreshing") {
      return (
        <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-hidden px-1 py-2 sm:px-2">
          {[...Array(8)].map((_, index) => (
            <Skeleton key={index} className="h-10 w-full shrink-0" />
          ))}
        </div>
      );
    }

    if (
      status === "unauthorized" ||
      status === "forbidden" ||
      status === "transient-error" ||
      status === "error"
    ) {
      return (
        <div className="min-h-0 flex-1 overflow-auto">
          <StatePanel
            title={
              status === "unauthorized"
                ? suspiciousCopy.states.unauthorizedTitle
                : status === "forbidden"
                  ? suspiciousCopy.states.forbiddenTitle
                  : status === "transient-error"
                    ? suspiciousCopy.states.transientTitle
                    : suspiciousCopy.states.loadErrorTitle
            }
            message={
              message ||
              (status === "unauthorized"
                ? suspiciousCopy.states.unauthorizedMessage
                : status === "forbidden"
                  ? suspiciousCopy.states.forbiddenMessage
                  : suspiciousCopy.states.transientMessage)
            }
            tone={status === "forbidden" ? "danger" : status === "transient-error" ? "warning" : "neutral"}
            action={
              status === "transient-error" || status === "error" ? (
                <Button variant="outline" onClick={reload}>
                  {dashboardCopy.states.retry}
                </Button>
              ) : undefined
            }
          />
        </div>
      );
    }

    if (status === "empty") {
      return (
        <div className="min-h-0 flex-1 overflow-auto">
          <EmptyState
            title={suspiciousCopy.states.emptyTitle}
            message={suspiciousCopy.states.emptyMessage}
          />
        </div>
      );
    }

    const paginationBar = (
      <SuspiciousListPagination
        page={state.page}
        totalPages={totalPages}
        resultRange={resultRange}
        onPageChange={setPage}
      />
    );

    return (
      <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-2 overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border border-border bg-card/70 px-3 py-2.5">
          <div className="min-w-0 space-y-0.5">
            <div className="text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
              {suspiciousCopy.labels.tableDisplayLegend}
            </div>
            <div className="text-[12px] text-foreground/82">{resultRange}</div>
          </div>
          <label className="inline-flex cursor-pointer select-none items-center gap-2 text-[12px] text-foreground/90">
            <input
              type="checkbox"
              className="h-3.5 w-3.5 shrink-0 rounded border-input accent-primary"
              checked={groupByReason}
              onChange={(event) => setGroupByReason(event.target.checked)}
            />
            <span className="whitespace-nowrap">{suspiciousCopy.labels.groupByReasonPattern}</span>
          </label>
        </div>
        <SuspiciousListTable
          title={countLabel}
          metricKey={metricKey}
          data={data}
          onOpenDetail={handleOpenDetail}
          groupByReason={groupByReason}
        />
        <div className="shrink-0">{paginationBar}</div>
      </div>
    );
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <PageHeader
        className="shrink-0"
        title={title}
        meta={state.date ? suspiciousCopy.targetDateMeta(state.date) : suspiciousCopy.targetDateMetaPending}
        status={pageStatus}
        actions={
          <>
            <DateQuickSelect
              value={state.date}
              onChange={setDate}
              availableDates={availableDates}
              showQuickButtons={false}
              className="gap-1.5"
            />
            <Button
              type="button"
              variant={searchPanelOpen ? "secondary" : "outline"}
              size="sm"
              className="h-9 shrink-0"
              aria-expanded={searchPanelOpen}
              aria-controls="suspicious-list-search-panel"
              onClick={() => setSearchPanelOpen((open) => !open)}
            >
              {suspiciousCopy.labels.searchOpenButton}
            </Button>
            <LastUpdated lastUpdated={lastUpdated} onRefresh={reload} isRefreshing={isRefreshing} compact />
          </>
        }
      />

      {searchPanelOpen ? (
        <div
          id="suspicious-list-search-panel"
          className="shrink-0 border-b border-border bg-muted/20 px-3 py-2.5 sm:px-4"
        >
          <Input
            ref={searchInputRef}
            type="search"
            name="search"
            aria-label={suspiciousCopy.labels.search}
            placeholder={suspiciousCopy.labels.searchPlaceholder}
            value={searchDraft}
            onChange={(event) => setSearchDraft(event.target.value)}
            className="h-9 max-w-xl"
          />
        </div>
      ) : null}

      <div className="flex min-h-0 flex-1 flex-col gap-1.5 overflow-hidden px-3 py-2 sm:px-4 sm:py-2.5">
        <div className="shrink-0">
          <SuspiciousListControls
            risk={state.risk}
            sort={state.sort}
            onRiskChange={setRisk}
            onSortChange={(value: SuspiciousSortValue) => setSort(value)}
          />
        </div>

        <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          {renderBody()}
        </div>
      </div>

      {/* ---- Detail drawer: スクリムは十分に不透明にし、パネルは min-h で隙間なく塗る（背後一覧との二重像を防ぐ） ---- */}
      {detailPanelState ? (
        <div
          className="fixed inset-0 z-50 overflow-y-auto overscroll-contain"
          role="dialog"
          aria-modal="true"
          aria-label={suspiciousCopy.labels.detailPanelTitle}
        >
          <div className="relative flex min-h-[100dvh] min-w-full justify-end">
            <div
              className="fc-detail-drawer-backdrop absolute inset-0 z-0"
              onClick={closeDetail}
              aria-label={suspiciousCopy.labels.closeDetailPanelBackdrop}
            />
            <aside className="fc-detail-drawer-panel relative z-10 flex min-h-[100dvh] w-full max-w-[40rem] shrink-0 flex-col overflow-x-hidden border-l border-border bg-card text-card-foreground shadow-2xl sm:rounded-l-2xl">
              <div className="flex shrink-0 items-center justify-between gap-3 border-b border-border bg-card px-3 py-2.5 sm:px-4">
                <div className="min-w-0">
                  <div className="text-xs font-semibold tracking-tight text-foreground">
                    {suspiciousCopy.labels.detailBreadcrumb}
                  </div>
                  <div className="mt-0.5 text-[11px] leading-snug text-muted-foreground">
                    {suspiciousCopy.labels.detailEscapeHint}
                  </div>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-8 shrink-0 border-border bg-transparent hover:bg-muted"
                  onClick={closeDetail}
                  aria-label={suspiciousCopy.labels.backToList}
                >
                  {suspiciousCopy.labels.backToList}
                </Button>
              </div>
              <div className="fc-detail-drawer-panel-body flex flex-1 flex-col bg-card px-3 py-3 sm:px-4">
                <SuspiciousRowDetails
                  key={expandedRow ?? "detail"}
                  item={detailPanelState.item}
                  status={detailPanelState.status}
                  detailError={detailPanelState.message}
                  variant="panel"
                />
              </div>
            </aside>
          </div>
        </div>
      ) : null}
    </div>
  );
}
