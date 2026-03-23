"use client";

import { Fragment, useMemo, useState } from "react";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { SuspiciousRowDetails } from "@/components/suspicious-row-details";
import { useSuspiciousList } from "@/hooks/use-suspicious-list";
import { SuspiciousItem, SuspiciousResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ControlBar } from "@/components/ui/control-bar";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { SectionFrame } from "@/components/ui/section-frame";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type MetricKey = "total_clicks" | "total_conversions";
type SuspiciousFetcher = (
  date?: string,
  limit?: number,
  offset?: number,
  search?: string
) => Promise<SuspiciousResponse>;

interface SuspiciousListPageProps {
  title: string;
  description?: string;
  countLabel: string;
  fetcher: SuspiciousFetcher;
  metricKey: MetricKey;
}

type RiskFilter = "all" | "high" | "medium" | "low";

const riskToneMap: Record<string, "high" | "medium" | "low" | "neutral"> = {
  high: "high",
  medium: "medium",
  low: "low",
};

const riskLabel = (item: SuspiciousItem) => item.risk_label || item.risk_level || "未分類";

export default function SuspiciousListPage({
  title,
  countLabel,
  fetcher,
  metricKey,
}: SuspiciousListPageProps) {
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");

  const {
    data: rawData,
    loading,
    error,
    date,
    availableDates,
    search,
    page,
    totalPages,
    lastUpdated,
    isRefreshing,
    expandedRow,
    canPrev,
    canNext,
    resultRange,
    handleRefresh,
    handleDateChange,
    handleSearchChange,
    toggleRow,
    goToFirstPage,
    goToPreviousPage,
    goToNextPage,
    goToLastPage,
  } = useSuspiciousList(fetcher);

  const data = useMemo(
    () =>
      riskFilter === "all"
        ? rawData
        : rawData.filter((item) => item.risk_level === riskFilter),
    [rawData, riskFilter]
  );

  const riskFilterButtons: { key: RiskFilter; label: string }[] = [
    { key: "all", label: "全件" },
    { key: "high", label: "高" },
    { key: "medium", label: "中" },
    { key: "low", label: "低" },
  ];

  return (
    <div className="flex h-full min-h-0 flex-col">
      <PageHeader
        title={title}
        meta={date ? `対象日 ${date}` : "対象日 -"}
        actions={
          <>
            <DateQuickSelect
              value={date}
              onChange={handleDateChange}
              availableDates={availableDates}
              showQuickButtons
            />
            <LastUpdated
              lastUpdated={lastUpdated}
              onRefresh={handleRefresh}
              isRefreshing={isRefreshing}
            />
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
                placeholder="IP / User-Agent / 媒体名"
                aria-label="一覧を検索"
                value={search}
                onChange={(event) => handleSearchChange(event.target.value)}
                autoComplete="off"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {riskFilterButtons.map(({ key, label }) => (
                <Button
                  key={key}
                  type="button"
                  size="sm"
                  variant={riskFilter === key ? "default" : "outline"}
                  onClick={() => setRiskFilter(key)}
                  aria-pressed={riskFilter === key}
                >
                  {label}
                </Button>
              ))}
            </div>

            <div className="w-full text-xs text-muted-foreground sm:ml-auto sm:w-auto">
              {resultRange}
            </div>
          </ControlBar>

          <SectionFrame bodyClassName="p-0">
            {error ? (
              <div className="border-b border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {error}
              </div>
            ) : null}

            {loading ? (
              <div className="space-y-2 p-4">
                {[...Array(6)].map((_, index) => (
                  <Skeleton key={index} className="h-11 w-full" />
                ))}
              </div>
            ) : data.length === 0 ? (
              <div className="p-4">
                <EmptyState title="該当なし" message="条件に一致する行がありません。" />
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-24">リスク</TableHead>
                      <TableHead className="w-[8.5rem]">IP</TableHead>
                      <TableHead className="hidden lg:table-cell lg:w-[30%]">User-Agent</TableHead>
                      <TableHead className="w-24 text-right">{countLabel}</TableHead>
                      <TableHead className="hidden xl:table-cell xl:w-20 text-right">
                        媒体数
                      </TableHead>
                      <TableHead className="hidden xl:table-cell xl:w-20 text-right">
                        案件数
                      </TableHead>
                      <TableHead className="hidden 2xl:table-cell 2xl:w-[24%]">
                        理由
                      </TableHead>
                      <TableHead className="w-28 text-right">詳細</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.map((item, index) => {
                      const rowKey = `${item.ipaddress}-${index}`;
                      const isExpanded = expandedRow === rowKey;

                      return (
                        <Fragment key={rowKey}>
                          <TableRow>
                            <TableCell>
                              <StatusBadge tone={riskToneMap[item.risk_level || ""] || "neutral"}>
                                {riskLabel(item)}
                              </StatusBadge>
                            </TableCell>
                            <TableCell
                              className="truncate font-mono text-[11px] text-foreground"
                              title={item.ipaddress}
                            >
                              {item.ipaddress}
                            </TableCell>
                            <TableCell
                              className="hidden truncate text-xs text-muted-foreground lg:table-cell"
                              title={item.useragent}
                            >
                              {item.useragent}
                            </TableCell>
                            <TableCell className="text-right font-semibold tabular-nums text-foreground">
                              {item[metricKey] ?? 0}
                            </TableCell>
                            <TableCell className="hidden text-right tabular-nums text-muted-foreground xl:table-cell">
                              {item.media_count}
                            </TableCell>
                            <TableCell className="hidden text-right tabular-nums text-muted-foreground xl:table-cell">
                              {item.program_count}
                            </TableCell>
                            <TableCell
                              className="hidden truncate text-xs text-muted-foreground 2xl:table-cell"
                              title={(item.reasons_formatted || item.reasons || []).join(" / ")}
                            >
                              {(item.reasons_formatted || item.reasons || []).slice(0, 2).join(" / ")}
                            </TableCell>
                            <TableCell className="text-right">
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => toggleRow(rowKey)}
                                aria-expanded={isExpanded}
                                className="min-w-[4.75rem] whitespace-nowrap px-2"
                              >
                                {isExpanded ? "閉じる" : "詳細"}
                              </Button>
                            </TableCell>
                          </TableRow>
                          {isExpanded ? (
                            <TableRow>
                              <TableCell colSpan={8} className="p-0">
                                <SuspiciousRowDetails item={item} />
                              </TableCell>
                            </TableRow>
                          ) : null}
                        </Fragment>
                      );
                    })}
                  </TableBody>
                </Table>

                <div className="flex flex-wrap items-center gap-2 border-t border-border px-4 py-3 text-xs text-muted-foreground">
                  <Button variant="outline" size="sm" onClick={goToFirstPage} disabled={!canPrev}>
                    最初
                  </Button>
                  <Button variant="outline" size="sm" onClick={goToPreviousPage} disabled={!canPrev}>
                    前へ
                  </Button>
                  <span className="px-2 tabular-nums">
                    {page} / {totalPages}
                  </span>
                  <Button variant="outline" size="sm" onClick={goToNextPage} disabled={!canNext}>
                    次へ
                  </Button>
                  <Button variant="outline" size="sm" onClick={goToLastPage} disabled={!canNext}>
                    最後
                  </Button>
                </div>
              </>
            )}
          </SectionFrame>
        </div>
      </div>
    </div>
  );
}
