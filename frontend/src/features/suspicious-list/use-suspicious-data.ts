"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { suspiciousCopy } from "@/copy/suspicious";
import {
  type SuspiciousQueryOptions,
  type SuspiciousResponse,
  getAvailableDates,
  getErrorMessage,
  toResourceIssue,
} from "@/lib/api";
import type {
  SuspiciousRiskFilter,
  SuspiciousSortOrder,
  SuspiciousSortValue,
} from "./url-state";

const PAGE_SIZE = 50;

type SuspiciousFetcher = (
  date?: string,
  limit?: number,
  offset?: number,
  options?: SuspiciousQueryOptions
) => Promise<SuspiciousResponse>;

export type SuspiciousDataStatus =
  | "loading"
  | "refreshing"
  | "ready"
  | "empty"
  | "unauthorized"
  | "forbidden"
  | "transient-error"
  | "error";

interface UseSuspiciousDataArgs {
  fetcher: SuspiciousFetcher;
  date: string;
  page: number;
  search: string;
  risk: SuspiciousRiskFilter;
  sort: SuspiciousSortValue;
  sortOrder: SuspiciousSortOrder;
}

export function useSuspiciousData({
  fetcher,
  date,
  page,
  search,
  risk,
  sort,
  sortOrder,
}: UseSuspiciousDataArgs) {
  const [data, setData] = useState<SuspiciousResponse["data"]>([]);
  const [total, setTotal] = useState(0);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [status, setStatus] = useState<SuspiciousDataStatus>("loading");
  const [message, setMessage] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadDates = useCallback(async () => {
    const result = await getAvailableDates();
    setAvailableDates(result.dates || []);
    return result.dates || [];
  }, []);

  const loadData = useCallback(
    async (refresh = false) => {
      setStatus(refresh ? "refreshing" : "loading");
      setMessage(null);

      try {
        const offset = (page - 1) * PAGE_SIZE;
        const response = await fetcher(date || undefined, PAGE_SIZE, offset, {
          search: search.trim() || undefined,
          riskLevel: risk === "all" ? undefined : risk,
          sortBy: sort,
          sortOrder,
          includeDetails: false,
          maskSensitive: true,
        });
        setData(response.data || []);
        setTotal(response.total || 0);
        setLastUpdated(new Date());
        setStatus((response.total || 0) > 0 ? "ready" : "empty");
      } catch (error) {
        const issue = toResourceIssue(error, suspiciousCopy.states.loadErrorTitle);
        setMessage(issue.message);
        setStatus(issue.kind);
      }
    },
    [date, fetcher, page, risk, search, sort, sortOrder]
  );

  useEffect(() => {
    void loadDates().catch((error) => {
      setStatus("error");
      setMessage(getErrorMessage(error, "対象日の取得に失敗しました。"));
    });
  }, [loadDates]);

  useEffect(() => {
    if (!date) return;
    void loadData();
  }, [date, page, search, risk, sort, sortOrder, loadData]);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total]);
  const resultRange = useMemo(() => {
    if (status === "loading" || status === "refreshing") return suspiciousCopy.states.loadingRange;
    if (total === 0) return suspiciousCopy.states.emptyRange;
    const start = (page - 1) * PAGE_SIZE + 1;
    const end = Math.min(start + data.length - 1, total);
    return `${start}-${end}件 / 全${total.toLocaleString()}件`;
  }, [data.length, page, status, total]);

  return {
    data,
    total,
    totalPages,
    availableDates,
    status,
    message,
    lastUpdated,
    resultRange,
    isRefreshing: status === "refreshing",
    reload: () => loadData(true),
  };
}
