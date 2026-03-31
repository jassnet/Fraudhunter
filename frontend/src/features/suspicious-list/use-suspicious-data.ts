"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { formatSuspiciousResultRange, suspiciousCopy } from "@/copy/suspicious";
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

/** 一覧の行数（慣習的なページサイズに寄せて認知負荷を下げる） */
export const SUSPICIOUS_LIST_PAGE_SIZE = 10;

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
        const offset = (page - 1) * SUSPICIOUS_LIST_PAGE_SIZE;
        const response = await fetcher(date || undefined, SUSPICIOUS_LIST_PAGE_SIZE, offset, {
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
      setMessage(getErrorMessage(error, "日付の一覧を取得できませんでした。"));
    });
  }, [loadDates]);

  useEffect(() => {
    if (!date) return;
    void loadData();
  }, [date, page, search, risk, sort, sortOrder, loadData]);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / SUSPICIOUS_LIST_PAGE_SIZE)), [total]);
  const resultRange = useMemo(() => {
    if (status === "loading" || status === "refreshing") return suspiciousCopy.states.loadingRange;
    if (total === 0) return suspiciousCopy.states.emptyRange;
    const start = (page - 1) * SUSPICIOUS_LIST_PAGE_SIZE + 1;
    const end = Math.min(start + data.length - 1, total);
    return formatSuspiciousResultRange(start, end, total);
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
