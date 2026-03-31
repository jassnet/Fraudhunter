"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { dashboardCopy } from "@/copy/dashboard";
import {
  type DailyStatsItem,
  type SummaryResponse,
  fetchDailyStats,
  fetchSummary,
  getAvailableDates,
  getErrorMessage,
  toResourceIssue,
} from "@/lib/api";

export type DashboardStatus =
  | "loading"
  | "refreshing"
  | "ready"
  | "empty"
  | "unauthorized"
  | "forbidden"
  | "transient-error"
  | "error";

interface DashboardDiagnostics {
  findingsStale: boolean;
  findingsFreshness: string | null;
  masterSyncAt: string | null;
  coverage: SummaryResponse["quality"] extends infer Q
    ? Q extends { click_ip_ua_coverage?: infer T }
      ? T
      : null
    : null;
  enrichment: SummaryResponse["quality"] extends infer Q
    ? Q extends { conversion_click_enrichment?: infer T }
      ? T
      : null
    : null;
  staleReasons: string[];
}

export function useDashboardData() {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStatsItem[]>([]);
  const [status, setStatus] = useState<DashboardStatus>("loading");
  const [message, setMessage] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState("");
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadDashboardData = useCallback(async (targetDate?: string, refresh = false) => {
    setMessage(null);
    setStatus(refresh ? "refreshing" : "loading");

      try {
        const [summaryData, dailyData] = await Promise.all([
          fetchSummary(targetDate),
          fetchDailyStats(14, targetDate),
        ]);
      setSummary(summaryData);
      setDailyStats(dailyData.data || []);
      setLastUpdated(new Date());

      if (!targetDate && summaryData.date) {
        setSelectedDate(summaryData.date);
      }

      setStatus(summaryData ? "ready" : "empty");
    } catch (error) {
      const issue = toResourceIssue(error, dashboardCopy.states.loadError);
      setMessage(issue.message);
      setStatus(issue.kind);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    const init = async () => {
      try {
        const result = await getAvailableDates();
        if (cancelled) return;

        const dates = result.dates || [];
        setAvailableDates(dates);

        const initialDate = dates[0];
        if (initialDate) {
          setSelectedDate(initialDate);
          await loadDashboardData(initialDate, true);
          return;
        }
      } catch (error) {
        if (!cancelled) {
          setStatus("error");
          setMessage(getErrorMessage(error, "日付の一覧を取得できませんでした。"));
        }
      }

      if (!cancelled) {
        await loadDashboardData();
      }
    };

    void init();

    return () => {
      cancelled = true;
    };
  }, [loadDashboardData]);

  const handleDateChange = useCallback(
    async (nextDate: string) => {
      setSelectedDate(nextDate);
      await loadDashboardData(nextDate, true);
    },
    [loadDashboardData]
  );

  const handleRefresh = useCallback(async () => {
    await loadDashboardData(selectedDate || undefined, true);
  }, [loadDashboardData, selectedDate]);

  const diagnostics = useMemo<DashboardDiagnostics>(() => {
    const quality = summary?.quality;
    return {
      findingsStale: Boolean(quality?.findings?.stale),
      findingsFreshness: quality?.findings?.findings_last_computed_at || null,
      masterSyncAt: quality?.master_sync?.last_synced_at || null,
      coverage: quality?.click_ip_ua_coverage || null,
      enrichment: quality?.conversion_click_enrichment || null,
      staleReasons: quality?.findings?.stale_reasons || [],
    };
  }, [summary]);

  return {
    summary,
    dailyStats,
    status,
    message,
    selectedDate,
    availableDates,
    lastUpdated,
    diagnostics,
    isRefreshing: status === "refreshing",
    handleDateChange,
    handleRefresh,
  };
}
