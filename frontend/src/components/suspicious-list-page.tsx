"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
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
import { getAvailableDates, getErrorMessage, SuspiciousItem, SuspiciousResponse } from "@/lib/api";

// Simple badge helper to avoid shared UI dependency
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

const PAGE_SIZE = 50;
const SEARCH_DEBOUNCE_MS = 350;

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
  const [data, setData] = useState<SuspiciousItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [date, setDate] = useState<string>("");
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => setDebouncedSearch(search), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [search]);

  const loadDates = useCallback(async () => {
    try {
      const result = await getAvailableDates();
      const dates = result.dates || [];
      setAvailableDates(dates);
      setDate((prev) => (prev && dates.includes(prev) ? prev : dates[0] || ""));
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load dates."));
    }
  }, []);

  const fetchData = useCallback(
    async (targetDate: string | undefined, pageNum: number, query?: string) => {
      setError(null);
      setLoading(true);
      try {
        const offset = (pageNum - 1) * PAGE_SIZE;
        const json = await fetcher(targetDate || undefined, PAGE_SIZE, offset, query || undefined);
        setData(json.data || []);
        setTotal(json.total || 0);
        if (!targetDate && json.date) setDate(json.date);
        setLastUpdated(new Date());
      } catch (err) {
        setError(getErrorMessage(err, "Failed to load data."));
      } finally {
        setLoading(false);
      }
    },
    [fetcher]
  );

  useEffect(() => {
    loadDates();
  }, [loadDates]);

  useEffect(() => {
    if (date) {
      fetchData(date, page, debouncedSearch);
    }
  }, [date, page, debouncedSearch, fetchData]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const canPrev = page > 1;
  const canNext = page < totalPages;

  const handleRefresh = useCallback(() => {
    fetchData(date, page, debouncedSearch);
  }, [date, page, debouncedSearch, fetchData]);

  const visibleRows = useMemo(() => data, [data]);

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
              onChange={(next) => {
                setPage(1);
                setDate(next);
              }}
              availableDates={availableDates}
              showQuickButtons
              className="w-full flex-wrap lg:w-auto lg:flex-nowrap"
            />
            <LastUpdated
              lastUpdated={lastUpdated}
              onRefresh={handleRefresh}
              isRefreshing={false}
              className="flex-wrap"
            />
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex-1">
              <Input
                name="search"
                type="search"
                placeholder="Search IP / UA"
                value={search}
                onChange={(e) => {
                  setPage(1);
                  setSearch(e.target.value);
                }}
                autoComplete="off"
                className="max-w-sm"
              />
            </div>
            <div className="text-xs text-muted-foreground">
              {total > 0 ? `${total.toLocaleString()} results` : "No results"}
            </div>
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
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {visibleRows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="h-24 text-center">
                        No data
                      </TableCell>
                    </TableRow>
                  ) : (
                    visibleRows.map((item, idx) => (
                      <TableRow key={`${item.ipaddress}-${idx}`}>
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
                        <TableCell className="max-w-[320px] truncate text-xs" title={(item.reasons_formatted || item.reasons || []).join(", ")}>
                          {(item.reasons_formatted || item.reasons || []).slice(0, 2).join(", ")}
                        </TableCell>
                      </TableRow>
                    ))
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
              <Button variant="outline" size="sm" onClick={() => setPage(1)} disabled={!canPrev}>
                First
              </Button>
              <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={!canPrev}>
                Prev
              </Button>
              <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={!canNext}>
                Next
              </Button>
              <Button variant="outline" size="sm" onClick={() => setPage(totalPages)} disabled={!canNext}>
                Last
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
