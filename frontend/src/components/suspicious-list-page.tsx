"use client";

import { Fragment, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { SuspiciousItem, SuspiciousResponse } from "@/lib/api";
import { SuspiciousRowDetails } from "@/components/suspicious-row-details";
import { useSuspiciousList } from "@/hooks/use-suspicious-list";

function Badge({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold tracking-[0.02em] ${className || ""}`}
    >
      {children}
    </span>
  );
}

type MetricKey = "total_clicks" | "total_conversions";
type SuspiciousFetcher = (
  date?: string,
  limit?: number,
  offset?: number,
  search?: string
) => Promise<SuspiciousResponse>;

interface SuspiciousListPageProps {
  title: string;
  description: string;
  countLabel: string;
  fetcher: SuspiciousFetcher;
  metricKey: MetricKey;
}

type RiskFilter = "all" | "high" | "medium" | "low";

const riskBadge = (item: SuspiciousItem) => {
  const level = item.risk_level || "unknown";
  const label = item.risk_label || level;
  const className =
    level === "high"
      ? "border-rose-200 bg-rose-50 text-rose-700"
      : level === "medium"
        ? "border-amber-200 bg-amber-50 text-amber-700"
        : level === "low"
          ? "border-sky-200 bg-sky-50 text-sky-700"
          : "border-muted bg-muted/50 text-muted-foreground";
  return <Badge className={className}>{label}</Badge>;
};

export default function SuspiciousListPage({
  title,
  description,
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

  const data = riskFilter === "all"
    ? rawData
    : rawData.filter((item) => item.risk_level === riskFilter);

  const riskFilterButtons: { key: RiskFilter; label: string }[] = [
    { key: "all", label: "全て" },
    { key: "high", label: "高リスク" },
    { key: "medium", label: "中リスク" },
    { key: "low", label: "低リスク" },
  ];

  return (
    <div>
      <header className="flex flex-wrap items-center gap-x-6 gap-y-3 border-b border-slate-200 px-6 py-5 sm:px-8">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-950">{title}</h1>
        <span className="text-sm text-slate-500">対象日: {date || "未選択"}</span>
        <div className="ml-auto flex flex-wrap items-center gap-3">
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
        </div>
      </header>

      <div className="p-6 sm:p-8">
        <Card className="border-slate-200 bg-white">
          <CardHeader className="space-y-4 border-b border-slate-100 pb-5">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-slate-700">検知一覧</p>
                <p className="text-xs text-muted-foreground">
                  IP アドレス、User-Agent、理由、関連メディアをまとめて確認できます。
                </p>
              </div>
              <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
                {resultRange}
              </div>
            </div>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex-1">
                <Input
                  name="search"
                  type="search"
                  placeholder="IP / User-Agent / メディア名で検索"
                  aria-label="不審一覧を検索"
                  value={search}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  autoComplete="off"
                  className="h-11 max-w-xl rounded-md border-slate-200 bg-white px-4"
                />
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {riskFilterButtons.map(({ key, label }) => (
                <Button
                  key={key}
                  type="button"
                  size="sm"
                  variant={riskFilter === key ? "default" : "outline"}
                  className="rounded-md"
                  onClick={() => setRiskFilter(key)}
                >
                  {label}
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            {error && (
              <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
                {error}
              </div>
            )}

            {loading ? (
              <div className="space-y-3">
                {[...Array(6)].map((_, i) => (
                  <Skeleton key={i} className="h-14 w-full rounded-xl" />
                ))}
              </div>
            ) : (
              <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50">
                      <TableHead>リスク</TableHead>
                      <TableHead>IP アドレス</TableHead>
                      <TableHead>User-Agent</TableHead>
                      <TableHead className="text-right">{countLabel}</TableHead>
                      <TableHead className="text-right">メディア数</TableHead>
                      <TableHead className="text-right">案件数</TableHead>
                      <TableHead>主な理由</TableHead>
                      <TableHead className="text-right">詳細</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="h-24 text-center text-sm text-muted-foreground">
                          該当データはありません
                        </TableCell>
                      </TableRow>
                    ) : (
                      data.map((item, idx) => {
                        const rowKey = `${item.ipaddress}-${idx}`;
                        const isExpanded = expandedRow === rowKey;
                        return (
                          <Fragment key={rowKey}>
                            <TableRow className="border-slate-100 align-top hover:bg-slate-50">
                              <TableCell className="py-3.5">{riskBadge(item)}</TableCell>
                              <TableCell className="py-3.5 font-mono text-xs text-slate-700">
                                {item.ipaddress}
                              </TableCell>
                              <TableCell
                                className="max-w-[320px] truncate py-3.5 text-xs text-slate-700"
                                title={item.useragent}
                              >
                                {item.useragent}
                              </TableCell>
                              <TableCell className="py-3.5 text-right font-semibold tabular-nums text-slate-900">
                                {item[metricKey] ?? 0}
                              </TableCell>
                              <TableCell className="py-3.5 text-right tabular-nums text-slate-700">
                                {item.media_count}
                              </TableCell>
                              <TableCell className="py-3.5 text-right tabular-nums text-slate-700">
                                {item.program_count}
                              </TableCell>
                              <TableCell
                                className="max-w-[320px] truncate py-3.5 text-xs text-slate-600"
                                title={(item.reasons_formatted || item.reasons || []).join(", ")}
                              >
                                {(item.reasons_formatted || item.reasons || []).slice(0, 2).join(" / ")}
                              </TableCell>
                              <TableCell className="py-3.5 text-right">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => toggleRow(rowKey)}
                                  aria-expanded={isExpanded}
                                  className="rounded-md border border-slate-200 bg-white hover:bg-slate-100"
                                >
                                  {isExpanded ? "閉じる" : "詳細"}
                                </Button>
                              </TableCell>
                            </TableRow>
                            {isExpanded ? (
                              <TableRow className="bg-slate-100">
                                <TableCell colSpan={8} className="p-4">
                                  <SuspiciousRowDetails item={item} />
                                </TableCell>
                              </TableRow>
                            ) : null}
                          </Fragment>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </div>
            )}

            <div className="mt-5 flex flex-wrap items-center gap-2 text-sm">
              <Button variant="outline" size="sm" onClick={goToFirstPage} disabled={!canPrev}>
                先頭
              </Button>
              <Button variant="outline" size="sm" onClick={goToPreviousPage} disabled={!canPrev}>
                前へ
              </Button>
              <span className="px-2 text-muted-foreground">{page} / {totalPages} ページ</span>
              <Button variant="outline" size="sm" onClick={goToNextPage} disabled={!canNext}>
                次へ
              </Button>
              <Button variant="outline" size="sm" onClick={goToLastPage} disabled={!canNext}>
                最後
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
