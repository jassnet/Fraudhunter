"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  SuspiciousItem,
  SuspiciousQueryOptions,
  SuspiciousResponse,
  getAvailableDates,
  getErrorMessage,
} from "@/lib/api";

const PAGE_SIZE = 50;
const SEARCH_DEBOUNCE_MS = 350;

type SuspiciousFetcher = (
  date?: string,
  limit?: number,
  offset?: number,
  options?: SuspiciousQueryOptions
) => Promise<SuspiciousResponse>;

interface UseSuspiciousListOptions {
  riskLevel?: SuspiciousQueryOptions["riskLevel"];
  sortBy?: SuspiciousQueryOptions["sortBy"];
  sortOrder?: SuspiciousQueryOptions["sortOrder"];
  includeDetails?: boolean;
}

export function useSuspiciousList(
  fetcher: SuspiciousFetcher,
  options: UseSuspiciousListOptions = {}
) {
  const {
    riskLevel,
    sortBy = "count",
    sortOrder = "desc",
    includeDetails = false,
  } = options;
  const [data, setData] = useState<SuspiciousItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [date, setDate] = useState("");
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [datesLoaded, setDatesLoaded] = useState(false);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

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
      setError(getErrorMessage(err, "対象日の取得に失敗しました。"));
    } finally {
      setDatesLoaded(true);
    }
  }, []);

  const loadData = useCallback(
    async (targetDate: string | undefined, pageNumber: number, query?: string, refresh = false) => {
      setError(null);
      setLoading(true);
      if (refresh) {
        setIsRefreshing(true);
      }

      try {
        const offset = (pageNumber - 1) * PAGE_SIZE;
        const response = await fetcher(targetDate || undefined, PAGE_SIZE, offset, {
          search: query || undefined,
          riskLevel,
          sortBy,
          sortOrder,
          includeDetails,
        });
        setData(response.data || []);
        setTotal(response.total || 0);
        if (!targetDate && response.date) {
          setDate(response.date);
        }
        setLastUpdated(new Date());
      } catch (err) {
        setError(getErrorMessage(err, "一覧データの取得に失敗しました。"));
      } finally {
        setLoading(false);
        if (refresh) {
          setIsRefreshing(false);
        }
      }
    },
    [fetcher, includeDetails, riskLevel, sortBy, sortOrder]
  );

  useEffect(() => {
    void loadDates();
  }, [loadDates]);

  useEffect(() => {
    if (!datesLoaded) {
      return;
    }
    void loadData(date || undefined, page, debouncedSearch, true);
  }, [date, page, debouncedSearch, datesLoaded, loadData]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const canPrev = page > 1;
  const canNext = page < totalPages;

  const resultRange = useMemo(() => {
    if (loading) {
      return "読み込み中...";
    }
    if (total === 0) {
      return "検索結果はありません";
    }
    if (data.length === 0) {
      return `0件 / 全${total.toLocaleString()}件`;
    }
    const start = (page - 1) * PAGE_SIZE + 1;
    const end = Math.min(start + data.length - 1, total);
    return `${start}-${end}件目 / 全${total.toLocaleString()}件`;
  }, [data.length, loading, page, total]);

  const handleRefresh = useCallback(async () => {
    await loadData(date || undefined, page, debouncedSearch, true);
  }, [date, debouncedSearch, loadData, page]);

  const handleDateChange = useCallback((nextDate: string) => {
    setPage(1);
    setExpandedRow(null);
    setDate(nextDate);
  }, []);

  const handleSearchChange = useCallback((nextSearch: string) => {
    setPage(1);
    setExpandedRow(null);
    setSearch(nextSearch);
  }, []);

  const toggleRow = useCallback((key: string) => {
    setExpandedRow((prev) => (prev === key ? null : key));
  }, []);

  const goToFirstPage = useCallback(() => {
    setExpandedRow(null);
    setPage(1);
  }, []);

  const goToPreviousPage = useCallback(() => {
    setExpandedRow(null);
    setPage((current) => Math.max(1, current - 1));
  }, []);

  const goToNextPage = useCallback(() => {
    setExpandedRow(null);
    setPage((current) => Math.min(totalPages, current + 1));
  }, [totalPages]);

  const goToLastPage = useCallback(() => {
    setExpandedRow(null);
    setPage(totalPages);
  }, [totalPages]);

  return {
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
  };
}
