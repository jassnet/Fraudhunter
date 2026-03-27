"use client";

import { Fragment, useEffect, useState } from "react";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { SuspiciousRowDetails } from "@/components/suspicious-row-details";
import { Button } from "@/components/ui/button";
import { ControlBar } from "@/components/ui/control-bar";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { SectionFrame } from "@/components/ui/section-frame";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/ui/state-panel";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { suspiciousCopy } from "@/copy/suspicious";
import { useSuspiciousData } from "@/features/suspicious-list/use-suspicious-data";
import { useSuspiciousDetails } from "@/features/suspicious-list/use-suspicious-details";
import {
  type SuspiciousRiskFilter,
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

const riskToneMap: Record<string, "high" | "medium" | "low" | "neutral"> = {
  high: "high",
  medium: "medium",
  low: "low",
};

const riskButtons: { key: SuspiciousRiskFilter; label: string }[] = [
  { key: "all", label: suspiciousCopy.labels.all },
  { key: "high", label: suspiciousCopy.labels.high },
  { key: "medium", label: suspiciousCopy.labels.medium },
  { key: "low", label: suspiciousCopy.labels.low },
];

function maskedValue(value?: string, masked?: string, isMasked?: boolean) {
  if (!isMasked) return value || "-";
  return masked || suspiciousCopy.labels.masked;
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

  const canPrev = state.page > 1;
  const canNext = state.page < totalPages;

  const pageStatus =
    status === "unauthorized" ? (
      <span className="text-[12px] text-[hsl(var(--warning))]">認証が必要です</span>
    ) : status === "forbidden" ? (
      <span className="text-[12px] text-destructive">権限不足</span>
    ) : null;

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
      <SectionFrame title={countLabel}>
        <div className="space-y-3">
          <div className="text-[12px] text-foreground/68">{suspiciousCopy.states.maskedHint}</div>
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[10rem]">IP</TableHead>
                <TableHead className="hidden w-[18rem] lg:table-cell">User-Agent</TableHead>
                <TableHead className="w-[10rem]">{countLabel}</TableHead>
                <TableHead className="hidden w-[7rem] md:table-cell">{suspiciousCopy.labels.risk}</TableHead>
                <TableHead className="hidden w-[9rem] xl:table-cell">{suspiciousCopy.labels.reasons}</TableHead>
                <TableHead className="w-28 text-right">{suspiciousCopy.labels.detail}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item) => {
                const rowKey = item.finding_key || `${item.ipaddress}-${item.useragent}`;
                const detailState = getDetailState(item);
                const isExpanded = expandedRow === rowKey;

                return (
                  <Fragment key={rowKey}>
                    <TableRow className={item.risk_level === "high" ? "bg-destructive/[0.04]" : ""}>
                      <TableCell className="font-mono text-[12px] text-foreground/92">
                        <div>{maskedValue(item.ipaddress, item.ipaddress_masked, item.sensitive_values_masked)}</div>
                        {item.sensitive_values_masked ? (
                          <div className="mt-1 text-[11px] text-foreground/58">{suspiciousCopy.labels.masked}</div>
                        ) : null}
                      </TableCell>
                      <TableCell className="hidden text-[12px] text-foreground/82 lg:table-cell">
                        {maskedValue(
                          item.useragent,
                          item.useragent_masked,
                          item.sensitive_values_masked
                        )}
                      </TableCell>
                      <TableCell className="tabular-nums text-[13px] text-foreground">
                        {metricKey === "total_clicks"
                          ? item.total_clicks?.toLocaleString()
                          : item.total_conversions?.toLocaleString()}
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        <StatusBadge tone={riskToneMap[item.risk_level || ""] || "neutral"}>
                          {item.risk_label || item.risk_level || "-"}
                        </StatusBadge>
                      </TableCell>
                      <TableCell className="hidden text-[12px] text-foreground/78 xl:table-cell">
                        {item.reasons_formatted?.[0] || item.reasons?.[0] || "-"}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={async () => {
                            const nextExpanded = isExpanded ? null : rowKey;
                            setExpandedRow(nextExpanded);
                            if (!isExpanded) {
                              await loadDetail(item);
                            }
                          }}
                          className="min-w-[4.75rem] whitespace-nowrap"
                        >
                          {isExpanded ? suspiciousCopy.labels.close : suspiciousCopy.labels.detail}
                        </Button>
                      </TableCell>
                    </TableRow>
                    {isExpanded ? (
                      <TableRow className="hover:bg-transparent">
                        <TableCell colSpan={6} className="p-0">
                          <SuspiciousRowDetails
                            item={detailState.item}
                            status={detailState.status}
                            detailError={detailState.message}
                          />
                        </TableCell>
                      </TableRow>
                    ) : null}
                  </Fragment>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </SectionFrame>
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
          <ControlBar>
            <div className="min-w-0 flex-1">
              <Input
                name="search"
                type="search"
                placeholder={suspiciousCopy.labels.searchPlaceholder}
                aria-label={suspiciousCopy.labels.search}
                value={searchDraft}
                onChange={(event) => setSearchDraft(event.target.value)}
                autoComplete="off"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {riskButtons.map((button) => (
                <Button
                  key={button.key}
                  type="button"
                  size="sm"
                  variant={state.risk === button.key ? "default" : "outline"}
                  onClick={() => setRisk(button.key)}
                >
                  {button.label}
                </Button>
              ))}
            </div>

            <select
              className="h-10 border border-input bg-card px-3 text-[13px] text-foreground outline-none transition-colors focus:border-white"
              value={state.sort}
              onChange={(event) => setSort(event.target.value as SuspiciousSortValue)}
              aria-label={suspiciousCopy.labels.sort}
            >
              <option value="count">{suspiciousCopy.labels.sortCount}</option>
              <option value="risk">{suspiciousCopy.labels.sortRisk}</option>
              <option value="latest">{suspiciousCopy.labels.sortLatest}</option>
            </select>

            <div
              aria-label="現在の結果範囲"
              className="w-full text-[13px] text-foreground/78 sm:ml-auto sm:w-auto"
            >
              {resultRange}
            </div>
          </ControlBar>

          {renderBody()}

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-3 text-[13px] text-foreground/78">
            <div aria-label="結果範囲" aria-live="polite">
              {resultRange}
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => setPage(1)} disabled={!canPrev}>
                最初
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setPage(Math.max(1, state.page - 1))}
                disabled={!canPrev}
              >
                前へ
              </Button>
              <span className="tabular-nums text-foreground/86">
                {state.page} / {totalPages}
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setPage(Math.min(totalPages, state.page + 1))}
                disabled={!canNext}
              >
                次へ
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setPage(totalPages)}
                disabled={!canNext}
              >
                最後
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
