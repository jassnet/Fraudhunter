"use client";

import { Fragment } from "react";
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
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${className || ""}`}>
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

const riskBadge = (item: SuspiciousItem) => {
  const level = item.risk_level || "unknown";
  const label = item.risk_label || level;
  const className =
    level === "high"
      ? "border-red-500/30 bg-red-500/10 text-red-600"
      : level === "medium"
        ? "border-yellow-500/30 bg-yellow-500/10 text-yellow-600"
        : level === "low"
          ? "border-blue-500/30 bg-blue-500/10 text-blue-600"
          : "border-muted text-muted-foreground";
  return <Badge className={className}>{label}</Badge>;
};

export default function SuspiciousListPage({
  title,
  description,
  countLabel,
  fetcher,
  metricKey,
}: SuspiciousListPageProps) {
  const {
    data,
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

  return (
    <div className="space-y-6 p-6 sm:p-8">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold">{title}</h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>

      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <DateQuickSelect
              value={date}
              onChange={handleDateChange}
              availableDates={availableDates}
              showQuickButtons
              className="w-full flex-wrap lg:w-auto lg:flex-nowrap"
            />
            <LastUpdated
              lastUpdated={lastUpdated}
              onRefresh={handleRefresh}
              isRefreshing={isRefreshing}
              className="flex-wrap"
            />
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex-1">
              <Input
                name="search"
                type="search"
                placeholder="Search IP / UA"
                aria-label="Search suspicious list"
                value={search}
                onChange={(e) => handleSearchChange(e.target.value)}
                autoComplete="off"
                className="max-w-sm"
              />
            </div>
            <div className="text-xs text-muted-foreground">{resultRange}</div>
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {loading ? (
            <div className="space-y-2">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Risk</TableHead>
                    <TableHead>IP</TableHead>
                    <TableHead>User Agent</TableHead>
                    <TableHead className="text-right">{countLabel}</TableHead>
                    <TableHead className="text-right">Media</TableHead>
                    <TableHead className="text-right">Programs</TableHead>
                    <TableHead>Reasons</TableHead>
                    <TableHead className="text-right">Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="h-24 text-center">
                        No data
                      </TableCell>
                    </TableRow>
                  ) : (
                    data.map((item, idx) => {
                      const rowKey = `${item.ipaddress}-${idx}`;
                      const isExpanded = expandedRow === rowKey;
                      return (
                        <Fragment key={rowKey}>
                          <TableRow>
                            <TableCell>{riskBadge(item)}</TableCell>
                            <TableCell className="font-mono text-xs">{item.ipaddress}</TableCell>
                            <TableCell className="max-w-[320px] truncate text-xs" title={item.useragent}>
                              {item.useragent}
                            </TableCell>
                            <TableCell className="text-right font-semibold tabular-nums">
                              {item[metricKey] ?? 0}
                            </TableCell>
                            <TableCell className="text-right tabular-nums">{item.media_count}</TableCell>
                            <TableCell className="text-right tabular-nums">{item.program_count}</TableCell>
                            <TableCell
                              className="max-w-[320px] truncate text-xs"
                              title={(item.reasons_formatted || item.reasons || []).join(", ")}
                            >
                              {(item.reasons_formatted || item.reasons || []).slice(0, 2).join(", ")}
                            </TableCell>
                            <TableCell className="text-right">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleRow(rowKey)}
                                aria-expanded={isExpanded}
                              >
                                {isExpanded ? "Hide" : "Details"}
                              </Button>
                            </TableCell>
                          </TableRow>
                          {isExpanded ? (
                            <TableRow className="bg-muted/30">
                              <TableCell colSpan={8}>
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

          <div className="mt-4 flex items-center justify-between text-sm">
            <div className="text-muted-foreground">
              Page {page} / {totalPages}
            </div>
            <div className="space-x-2">
              <Button variant="outline" size="sm" onClick={goToFirstPage} disabled={!canPrev}>
                First
              </Button>
              <Button variant="outline" size="sm" onClick={goToPreviousPage} disabled={!canPrev}>
                Prev
              </Button>
              <Button variant="outline" size="sm" onClick={goToNextPage} disabled={!canNext}>
                Next
              </Button>
              <Button variant="outline" size="sm" onClick={goToLastPage} disabled={!canNext}>
                Last
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
