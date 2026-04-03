"use client";

import { useEffect, useState } from "react";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { ListPageLayout } from "@/components/list-page-layout";
import { ListPageSearchBar } from "@/components/list-page-search-bar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { suspiciousCopy } from "@/features/suspicious-list/copy";
import { SuspiciousDetailDrawer } from "@/features/suspicious-list/suspicious-detail-drawer";
import { SuspiciousListContent } from "@/features/suspicious-list/suspicious-list-content";
import { SuspiciousListControls } from "@/features/suspicious-list/suspicious-list-controls";
import { useSuspiciousListDisplayState } from "@/features/suspicious-list/use-suspicious-list-display-state";
import {
  type SuspiciousSortValue,
  useSuspiciousListUrlState,
} from "@/features/suspicious-list/url-state";
import {
  useSuspiciousData,
} from "@/features/suspicious-list/use-suspicious-data";
import { useSuspiciousDetails } from "@/features/suspicious-list/use-suspicious-details";
import {
  fetchSuspiciousConversionDetail,
  fetchSuspiciousConversions,
  type SuspiciousItem,
} from "@/lib/api";

function getRowKey(item: SuspiciousItem) {
  return item.finding_key || `${item.ipaddress}-${item.useragent}`;
}

export default function SuspiciousListPage() {
  const { state, setDate, setPage, setRisk, setSearch, setSort } = useSuspiciousListUrlState();
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const {
    groupByReason,
    searchDraft,
    searchInputRef,
    searchPanelOpen,
    setSearchDraft,
    setSearchPanelOpen,
    handleGroupByReasonChange,
  } = useSuspiciousListDisplayState({
    page: state.page,
    search: state.search,
    onPageChange: setPage,
    onSearchCommit: setSearch,
  });

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
    fetcher: fetchSuspiciousConversions,
    date: state.date,
    page: state.page,
    groupByReason,
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

  const { loadDetail, getDetailState } = useSuspiciousDetails(fetchSuspiciousConversionDetail);

  const detailPanelState = expandedRow
    ? (() => {
        const item = data.find((row) => getRowKey(row) === expandedRow);
        return item ? getDetailState(item) : null;
      })()
    : null;

  const pageStatus =
    status === "unauthorized" ? (
      <span className="text-[12px] text-[hsl(var(--warning))]">
        {suspiciousCopy.states.unauthorizedTitle}
      </span>
    ) : status === "forbidden" ? (
      <span className="text-[12px] text-destructive">
        {suspiciousCopy.states.forbiddenTitle}
      </span>
    ) : null;

  const handleOpenDetail = async (item: SuspiciousItem) => {
    setExpandedRow(getRowKey(item));
    await loadDetail(item);
  };

  const closeDetail = () => setExpandedRow(null);

  return (
    <>
      <ListPageLayout
        title={suspiciousCopy.conversionsTitle}
        meta={
          state.date
            ? suspiciousCopy.targetDateMeta(state.date)
            : suspiciousCopy.targetDateMetaPending
        }
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
            <LastUpdated
              lastUpdated={lastUpdated}
              onRefresh={reload}
              isRefreshing={isRefreshing}
              compact
            />
          </>
        }
        searchBar={
          searchPanelOpen ? (
            <ListPageSearchBar id="suspicious-list-search-panel">
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
            </ListPageSearchBar>
          ) : null
        }
      >
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
            <SuspiciousListContent
              data={data}
              groupByReason={groupByReason}
              message={message}
              page={state.page}
              resultRange={resultRange}
              status={status}
              totalPages={totalPages}
              onGroupByReasonChange={handleGroupByReasonChange}
              onOpenDetail={handleOpenDetail}
              onPageChange={setPage}
              onRetry={reload}
            />
          </div>
        </div>
      </ListPageLayout>

      {detailPanelState ? (
        <SuspiciousDetailDrawer
          item={detailPanelState.item}
          itemKey={expandedRow ?? "detail"}
          status={detailPanelState.status}
          detailError={detailPanelState.message}
          onClose={closeDetail}
        />
      ) : null}
    </>
  );
}
