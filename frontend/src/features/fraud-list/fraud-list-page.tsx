"use client";

import { useEffect, useState } from "react";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { ListPageLayout } from "@/components/list-page-layout";
import { ListPageSearchBar } from "@/components/list-page-search-bar";
import { Input } from "@/components/ui/input";
import { fraudCopy } from "@/features/fraud-list/copy";
import { FraudFindingDetailPanel } from "@/features/fraud-list/fraud-finding-detail-panel";
import { FraudFindingsContent } from "@/features/fraud-list/fraud-findings-content";
import { useFraudFindingDetails } from "@/features/fraud-list/use-fraud-finding-details";
import { useFraudFindingsData } from "@/features/fraud-list/use-fraud-findings-data";
import { SuspiciousListControls } from "@/features/suspicious-list/suspicious-list-controls";
import {
  type SuspiciousSortValue,
  useSuspiciousListUrlState,
} from "@/features/suspicious-list/url-state";

export default function FraudListPage() {
  const { state, setDate, setPage, setRisk, setSearch, setSort } = useSuspiciousListUrlState();
  const [searchDraft, setSearchDraft] = useState(state.search);
  const { selectedItem, detailStatus, detailMessage, openDetail, clearDetail } = useFraudFindingDetails();
  const {
    data,
    availableDates,
    status,
    message,
    lastUpdated,
    resolvedDate,
    totalPages,
    resultRange,
    reload,
  } = useFraudFindingsData({
    date: state.date,
    page: state.page,
    risk: state.risk,
    search: state.search,
    sort: state.sort,
    sortOrder: state.sortOrder,
  });

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      if (searchDraft !== state.search) {
        setSearch(searchDraft);
      }
    }, 300);

    return () => window.clearTimeout(timeoutId);
  }, [searchDraft, setSearch, state.search]);

  useEffect(() => {
    if (!state.date && resolvedDate) {
      setDate(resolvedDate);
    }
  }, [resolvedDate, setDate, state.date]);

  const hasDetailPanel = Boolean(selectedItem) || detailStatus === "loading" || detailStatus === "error";

  return (
    <ListPageLayout
      title={fraudCopy.title}
      meta={state.date ? fraudCopy.targetDateMeta(state.date) : fraudCopy.targetDateMetaPending}
      actions={
        <>
          <DateQuickSelect
            value={state.date}
            onChange={setDate}
            availableDates={availableDates}
            showQuickButtons={false}
            className="gap-1.5"
          />
          <LastUpdated lastUpdated={lastUpdated} onRefresh={reload} compact />
        </>
      }
      searchBar={
        <ListPageSearchBar>
          <Input
            type="search"
            aria-label={fraudCopy.labels.search}
            placeholder={fraudCopy.labels.searchPlaceholder}
            value={searchDraft}
            onChange={(event) => setSearchDraft(event.target.value)}
            className="h-9 max-w-xl"
          />
        </ListPageSearchBar>
      }
    >
      <div className="min-h-0 flex-1 overflow-auto p-4">
        <div className="grid gap-4 2xl:grid-cols-[minmax(0,1fr)_22rem]">
          <div className="min-w-0 space-y-3">
            <SuspiciousListControls
              risk={state.risk}
              sort={state.sort}
              onRiskChange={setRisk}
              onSortChange={(value: SuspiciousSortValue) => setSort(value)}
            />
            <FraudFindingsContent
              data={data}
              message={message}
              page={state.page}
              resultRange={resultRange}
              status={status}
              totalPages={totalPages}
              onOpenDetail={openDetail}
              onPageChange={setPage}
              onRetry={reload}
            />
          </div>

          {hasDetailPanel ? (
            <FraudFindingDetailPanel
              item={selectedItem}
              status={detailStatus}
              message={detailMessage}
              onClose={clearDetail}
              className="2xl:sticky 2xl:top-4 2xl:self-start"
            />
          ) : null}
        </div>
      </div>
    </ListPageLayout>
  );
}
