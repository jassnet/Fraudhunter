"use client";

import { useCallback, useEffect, useState } from "react";
import { dashboardCopy } from "@/features/dashboard/copy";
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
  coverage: SummaryResponse["quality"] extends infer T
    ? T extends { click_ip_ua_coverage?: infer U }
      ? U
      : null
    : null;
  enrichment: SummaryResponse["quality"] extends infer T
    ? T extends { conversion_click_enrichment?: infer U }
      ? U
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
    let active = true;

    const init = async () => {
      try {
        const result = await getAvailableDates();
        if (!active) return;

        const dates = result.dates || [];
        setAvailableDates(dates);

        const initialDate = dates[0];
        if (initialDate) {
          setSelectedDate(initialDate);
          await loadDashboardData(initialDate, true);
          return;
        }
      } catch (error) {
        if (!active) return;
        setStatus("error");
        setMessage(getErrorMessage(error, "Could not load the available dates."));
        return;
      }

      if (!active) return;
      await loadDashboardData();
    };

    void init();

    return () => {
      active = false;
    };
  }, [loadDashboardData]);

  const handleDateChange = async (nextDate: string) => {
    setSelectedDate(nextDate);
    await loadDashboardData(nextDate, true);
  };

  const handleRefresh = async () => {
    await loadDashboardData(selectedDate || undefined, true);
  };

  const quality = summary?.quality;
  const diagnostics: DashboardDiagnostics = {
    findingsStale: Boolean(quality?.findings?.stale),
    findingsFreshness: quality?.findings?.findings_last_computed_at || null,
    masterSyncAt: quality?.master_sync?.last_synced_at || null,
    coverage: quality?.click_ip_ua_coverage || null,
    enrichment: quality?.conversion_click_enrichment || null,
    staleReasons: quality?.findings?.stale_reasons || [],
  };

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
