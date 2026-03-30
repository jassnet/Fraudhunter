"use client";

import { useEffect, useState } from "react";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { SuspiciousListControls } from "@/components/suspicious-list-controls";
import { SuspiciousListPagination } from "@/components/suspicious-list-pagination";
import { SuspiciousListTable } from "@/components/suspicious-list-table";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { SectionFrame } from "@/components/ui/section-frame";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/ui/state-panel";
import { suspiciousCopy } from "@/copy/suspicious";
import { useSuspiciousData } from "@/features/suspicious-list/use-suspicious-data";
import { useSuspiciousDetails } from "@/features/suspicious-list/use-suspicious-details";
import {
  type SuspiciousSortValue,
  useSuspiciousListUrlState,
} from "@/features/suspicious-list/url-state";
import type { SuspiciousItem, SuspiciousQueryOptions, SuspiciousResponse } from "@/lib/api";

type MetricKey = "total_clicks" | "total_conversions";
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
  const [searchDraft, setSearchDraft] = useState(state.search);

  useEffect(() => {
    setSearchDraft(state.search);
  }, [state.search]);

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

  const { loadDetail, getDetailState } = useSuspiciousDetails(fetchDetail);

  const pageStatus =
    status === "unauthorized" ? (
      <span className="text-[12px] text-[hsl(var(--warning))]">{suspiciousCopy.states.unauthorizedTitle}</span>
    ) : status === "forbidden" ? (
      <span className="text-[12px] text-destructive">{suspiciousCopy.states.forbiddenTitle}</span>
    ) : null;

  const handleToggleRow = async (
    item: SuspiciousItem,
    rowKey: string,
    isExpanded: boolean
  ) => {
    const nextExpanded = isExpanded ? null : rowKey;
    setExpandedRow(nextExpanded);
    if (!isExpanded) {
      await loadDetail(item);
    }
  };

  const renderBody = () => {
    if (status === "loading" || status === "refreshing") {
      return (
        <SectionFrame title={countLabel}>
          <div className="space-y-3">
            {[...Array(6)].map((_, index) => (
              <Skeleton key={index} className="h-11 w-full" />
            ))}
          </div>
        </SectionFrame>
      );
    }

    if (
      status === "unauthorized" ||
      status === "forbidden" ||
      status === "transient-error" ||
      status === "error"
    ) {
      return (
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
                再読込
              </Button>
            ) : undefined
          }
        />
      );
    }

    if (status === "empty") {
      return (
        <EmptyState
          title={suspiciousCopy.states.emptyTitle}
          message={suspiciousCopy.states.emptyMessage}
        />
      );
    }

    return (
      <SuspiciousListTable
        title={countLabel}
        metricKey={metricKey}
        data={data}
        expandedRow={expandedRow}
        getDetailState={getDetailState}
        onToggleRow={handleToggleRow}
      />
    );
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <PageHeader
        title={title}
        meta={state.date ? `対象日 ${state.date}` : "対象日 -"}
        status={pageStatus}
        actions={
          <>
            <DateQuickSelect
              value={state.date}
              onChange={setDate}
              availableDates={availableDates}
              showQuickButtons
            />
            <LastUpdated lastUpdated={lastUpdated} onRefresh={reload} isRefreshing={isRefreshing} />
          </>
        }
      />

      <div className="min-h-0 flex-1 overflow-auto">
        <div className="space-y-4 p-4 sm:p-6">
          <SuspiciousListControls
            searchDraft={searchDraft}
            resultRange={resultRange}
            risk={state.risk}
            sort={state.sort}
            onSearchChange={setSearchDraft}
            onRiskChange={setRisk}
            onSortChange={(value: SuspiciousSortValue) => setSort(value)}
          />

          {renderBody()}

          <SuspiciousListPagination
            page={state.page}
            totalPages={totalPages}
            resultRange={resultRange}
            onPageChange={setPage}
          />
        </div>
      </div>
    </div>
  );
}
