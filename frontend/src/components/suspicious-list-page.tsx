"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Fragment, useEffect, useMemo, useState } from "react";

import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { SuspiciousRowDetails } from "@/components/suspicious-row-details";
import { useSuspiciousList } from "@/hooks/use-suspicious-list";
import {
  SuspiciousItem,
  SuspiciousQueryOptions,
  SuspiciousResponse,
  getErrorMessage,
} from "@/lib/api";
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
type RiskFilter = "all" | "high" | "medium" | "low";
type SortValue = "count" | "risk" | "latest";
type SuspiciousFetcher = (
  date?: string,
  limit?: number,
  offset?: number,
  options?: SuspiciousQueryOptions
) => Promise<SuspiciousResponse>;
type SuspiciousDetailFetcher = (findingKey: string) => Promise<SuspiciousItem>;

interface SuspiciousListPageProps {
  title: string;
  description?: string;
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

const riskFilterButtons: {
  key: RiskFilter;
  label: string;
  activeClass?: string;
  inactiveClass?: string;
}[] = [
  { key: "all", label: "すべて" },
  {
    key: "high",
    label: "高",
    activeClass: "border-destructive bg-destructive text-destructive-foreground hover:bg-destructive/90",
    inactiveClass: "border-destructive/60 text-destructive hover:bg-destructive/10",
  },
  {
    key: "medium",
    label: "中",
    activeClass: "border-[hsl(var(--warning))] bg-[hsl(var(--warning))] text-[hsl(var(--warning-foreground))] hover:bg-[hsl(var(--warning))]/90",
    inactiveClass: "border-[hsl(var(--warning))]/60 text-[hsl(var(--warning))] hover:bg-[hsl(var(--warning))]/10",
  },
  {
    key: "low",
    label: "低",
    activeClass: "border-[hsl(var(--success))] bg-[hsl(var(--success))] text-[hsl(var(--success-foreground))] hover:bg-[hsl(var(--success))]/90",
    inactiveClass: "border-[hsl(var(--success))]/60 text-[hsl(var(--success))] hover:bg-[hsl(var(--success))]/10",
  },
];

const riskRowBg: Record<string, string> = {
  high: "bg-destructive/[0.07]",
};

const riskCellBorder: Record<string, string> = {
  high: "border-l-[3px] border-l-destructive",
  medium: "border-l-[3px] border-l-[hsl(var(--warning))]",
  low: "border-l-[3px] border-l-[hsl(var(--success))]",
};

const riskLabel = (item: SuspiciousItem) => item.risk_label || item.risk_level || "未判定";

function parseRiskFilter(value: string | null): RiskFilter {
  return value === "high" || value === "medium" || value === "low" ? value : "all";
}

function parseSortValue(value: string | null): SortValue {
  return value === "risk" || value === "latest" ? value : "count";
}

function parsePageValue(value: string | null): number {
  if (!value) {
    return 1;
  }
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 1;
}

export default function SuspiciousListPage({
  title,
  countLabel,
  fetcher,
  fetchDetail,
  metricKey,
}: SuspiciousListPageProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const initialDate = searchParams.get("date") || "";
  const initialSearch = searchParams.get("search") || "";
  const initialPage = parsePageValue(searchParams.get("page"));
  const [riskFilter, setRiskFilter] = useState<RiskFilter>(() =>
    parseRiskFilter(searchParams.get("risk"))
  );
  const [sortBy, setSortBy] = useState<SortValue>(() =>
    parseSortValue(searchParams.get("sort"))
  );
  const [detailCache, setDetailCache] = useState<Record<string, SuspiciousItem>>({});
  const [detailErrorByKey, setDetailErrorByKey] = useState<Record<string, string | null>>({});
  const [detailLoadingKey, setDetailLoadingKey] = useState<string | null>(null);

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
  } = useSuspiciousList(fetcher, {
    riskLevel: riskFilter === "all" ? undefined : riskFilter,
    sortBy,
    sortOrder: "desc",
    includeDetails: false,
    maskSensitive: true,
    initialDate,
    initialSearch,
    initialPage,
  });

  useEffect(() => {
    const params = new URLSearchParams(searchParams.toString());
    if (date) {
      params.set("date", date);
    } else {
      params.delete("date");
    }
    if (search.trim()) {
      params.set("search", search.trim());
    } else {
      params.delete("search");
    }
    if (page > 1) {
      params.set("page", String(page));
    } else {
      params.delete("page");
    }
    if (riskFilter !== "all") {
      params.set("risk", riskFilter);
    } else {
      params.delete("risk");
    }
    if (sortBy !== "count") {
      params.set("sort", sortBy);
    } else {
      params.delete("sort");
    }

    const nextQuery = params.toString();
    if (nextQuery !== searchParams.toString()) {
      router.replace(nextQuery ? `${pathname}?${nextQuery}` : pathname, { scroll: false });
    }
  }, [date, page, pathname, riskFilter, router, search, searchParams, sortBy]);

  const data = useMemo(
    () =>
      rawData.map((item) => {
        if (!item.finding_key) {
          return item;
        }
        const cached = detailCache[item.finding_key];
        return cached ? { ...item, ...cached } : item;
      }),
    [detailCache, rawData]
  );

  const handleRiskFilterChange = (nextRisk: RiskFilter) => {
    goToFirstPage();
    setRiskFilter(nextRisk);
  };

  const handleSortChange = (nextSort: SortValue) => {
    goToFirstPage();
    setSortBy(nextSort);
  };

  const handleToggleRow = async (item: SuspiciousItem, rowKey: string) => {
    const isExpanded = expandedRow === rowKey;
    toggleRow(rowKey);

    if (
      isExpanded ||
      !item.finding_key ||
      item.details?.length ||
      detailCache[item.finding_key]?.details?.length
    ) {
      return;
    }

    setDetailLoadingKey(rowKey);
    setDetailErrorByKey((current) => ({ ...current, [rowKey]: null }));
    try {
      const detailItem = await fetchDetail(item.finding_key);
      setDetailCache((current) => ({ ...current, [item.finding_key as string]: detailItem }));
    } catch (fetchError) {
      setDetailErrorByKey((current) => ({
        ...current,
        [rowKey]: getErrorMessage(fetchError, "詳細の取得に失敗しました。"),
      }));
    } finally {
      setDetailLoadingKey((current) => (current === rowKey ? null : current));
    }
  };

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
                placeholder="IP / User-Agent / 媒体 / 案件"
                aria-label="一覧を検索"
                value={search}
                onChange={(event) => handleSearchChange(event.target.value)}
                autoComplete="off"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {riskFilterButtons.map(({ key, label, activeClass, inactiveClass }) => (
                <Button
                  key={key}
                  type="button"
                  size="sm"
                  variant={riskFilter === key ? "default" : "outline"}
                  onClick={() => handleRiskFilterChange(key)}
                  aria-pressed={riskFilter === key}
                  className={riskFilter === key ? (activeClass ?? "") : (inactiveClass ?? "")}
                >
                  {label}
                </Button>
              ))}
            </div>

            <select
              className="h-10 border border-input bg-card px-3 text-[13px] text-foreground outline-none transition-colors focus:border-white"
              value={sortBy}
              onChange={(event) => handleSortChange(event.target.value as SortValue)}
              aria-label="並び順"
            >
              <option value="count">件数順</option>
              <option value="risk">リスク順</option>
              <option value="latest">最新順</option>
            </select>

            <div className="w-full text-[13px] text-foreground/78 sm:ml-auto sm:w-auto">
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
                <EmptyState title="該当なし" message="条件に一致する結果はありません。" />
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-24">リスク</TableHead>
                      <TableHead className="w-[8.5rem]">IP</TableHead>
                      <TableHead className="hidden lg:table-cell lg:w-[30%]">
                        User-Agent
                      </TableHead>
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
                      const rowKey = item.finding_key || `${item.ipaddress}-${index}`;
                      const isExpanded = expandedRow === rowKey;

                      return (
                        <Fragment key={rowKey}>
                          <TableRow className={riskRowBg[item.risk_level || ""] ?? ""}>
                            <TableCell className={riskCellBorder[item.risk_level || ""] ?? "border-l-[3px] border-l-transparent"}>
                              <StatusBadge
                                tone={riskToneMap[item.risk_level || ""] || "neutral"}
                              >
                                {riskLabel(item)}
                              </StatusBadge>
                            </TableCell>
                            <TableCell
                              className="truncate font-mono text-[12px] text-foreground"
                              title={item.ipaddress}
                            >
                              {item.ipaddress}
                            </TableCell>
                            <TableCell
                              className="hidden truncate text-[13px] text-foreground/82 lg:table-cell"
                              title={item.useragent}
                            >
                              {item.useragent}
                            </TableCell>
                            <TableCell className="text-right font-semibold tabular-nums text-foreground">
                              {item[metricKey] ?? 0}
                            </TableCell>
                            <TableCell className="hidden text-right tabular-nums text-foreground/76 xl:table-cell">
                              {item.media_count}
                            </TableCell>
                            <TableCell className="hidden text-right tabular-nums text-foreground/76 xl:table-cell">
                              {item.program_count}
                            </TableCell>
                            <TableCell
                              className="hidden truncate text-[13px] text-foreground/82 2xl:table-cell"
                              title={(item.reasons_formatted || item.reasons || []).join(" / ")}
                            >
                              {(item.reasons_formatted || item.reasons || []).slice(0, 2).join(" / ")}
                            </TableCell>
                            <TableCell className="text-right">
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => void handleToggleRow(item, rowKey)}
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
                                <SuspiciousRowDetails
                                  item={item}
                                  isLoadingDetails={detailLoadingKey === rowKey}
                                  detailError={detailErrorByKey[rowKey]}
                                />
                              </TableCell>
                            </TableRow>
                          ) : null}
                        </Fragment>
                      );
                    })}
                  </TableBody>
                </Table>

                <div className="flex flex-wrap items-center gap-2 border-t border-border bg-white/[0.03] px-4 py-3 text-[13px] text-foreground/82">
                  <Button variant="outline" size="sm" onClick={goToFirstPage} disabled={!canPrev}>
                    先頭
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={goToPreviousPage}
                    disabled={!canPrev}
                  >
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
