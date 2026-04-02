"use client";

import { useCallback, useEffect, useEffectEvent, useMemo, useState } from "react";
import {
  formatSuspiciousResultRange,
  suspiciousCopy,
} from "@/features/suspicious-list/copy";
import { clusterSuspiciousItems } from "@/features/suspicious-list/reason-cluster";
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

export const SUSPICIOUS_LIST_PAGE_SIZE = 7;
const SUSPICIOUS_GROUPED_FETCH_LIMIT = 10_000;

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
  groupByReason: boolean;
  search: string;
  risk: SuspiciousRiskFilter;
  sort: SuspiciousSortValue;
  sortOrder: SuspiciousSortOrder;
}

export function useSuspiciousData({
  fetcher,
  date,
  page,
  groupByReason,
  search,
  risk,
  sort,
  sortOrder,
}: UseSuspiciousDataArgs) {
  const [data, setData] = useState<SuspiciousResponse["data"]>([]);
  const [total, setTotal] = useState(0);
  const [visibleCount, setVisibleCount] = useState(0);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [status, setStatus] = useState<SuspiciousDataStatus>("loading");
  const [message, setMessage] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const executeLoadData = useCallback(async (refresh = false) => {
    setStatus(refresh ? "refreshing" : "loading");
    setMessage(null);

    try {
      const options: SuspiciousQueryOptions = {
        search: search.trim() || undefined,
        riskLevel: risk === "all" ? undefined : risk,
        sortBy: sort,
        sortOrder,
        includeDetails: false,
        maskSensitive: true,
      };

      if (groupByReason) {
        const response = await fetcher(date || undefined, SUSPICIOUS_GROUPED_FETCH_LIMIT, 0, options);
        const groups = clusterSuspiciousItems(response.data || []);
        const offset = (page - 1) * SUSPICIOUS_LIST_PAGE_SIZE;
        const pagedGroups = groups.slice(offset, offset + SUSPICIOUS_LIST_PAGE_SIZE);

        setData(pagedGroups.flatMap((group) => group.members));
        setTotal(groups.length);
        setVisibleCount(pagedGroups.length);
        setLastUpdated(new Date());
        setStatus(groups.length > 0 ? "ready" : "empty");
        return;
      }

      const offset = (page - 1) * SUSPICIOUS_LIST_PAGE_SIZE;
      const response = await fetcher(date || undefined, SUSPICIOUS_LIST_PAGE_SIZE, offset, options);

      setData(response.data || []);
      setTotal(response.total || 0);
      setVisibleCount((response.data || []).length);
      setLastUpdated(new Date());
      setStatus((response.total || 0) > 0 ? "ready" : "empty");
    } catch (error) {
      const issue = toResourceIssue(error, suspiciousCopy.states.loadErrorTitle);
      setMessage(issue.message);
      setStatus(issue.kind);
    }
  }, [date, fetcher, groupByReason, page, risk, search, sort, sortOrder]);

  const loadDates = useEffectEvent(async () => {
    try {
      const result = await getAvailableDates();
      setAvailableDates(result.dates || []);
    } catch (error) {
      setStatus("error");
      setMessage(getErrorMessage(error, "Could not load the available dates."));
    }
  });

  const loadData = useEffectEvent(async () => {
    await executeLoadData(false);
  });

  useEffect(() => {
    void loadDates();
  }, []);

  useEffect(() => {
    if (!date) return;
    void loadData();
  }, [date, page, risk, search, sort, sortOrder]);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(total / SUSPICIOUS_LIST_PAGE_SIZE)),
    [total]
  );
  const resultRange = useMemo(() => {
    if (status === "loading" || status === "refreshing") return suspiciousCopy.states.loadingRange;
    if (total === 0) return suspiciousCopy.states.emptyRange;
    const start = (page - 1) * SUSPICIOUS_LIST_PAGE_SIZE + 1;
    const end = Math.min(start + visibleCount - 1, total);
    return formatSuspiciousResultRange(start, end, total);
  }, [page, status, total, visibleCount]);

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
    reload: () => void executeLoadData(true),
  };
}
