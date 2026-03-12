"use client";

import { useCallback, useEffect, useState } from "react";
import {
  DailyStatsItem,
  SummaryResponse,
  fetchDailyStats,
  fetchSummary,
  getAvailableDates,
  getErrorMessage,
} from "@/lib/api";

export function useDashboardData() {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStatsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState("");
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadDashboardData = useCallback(async (targetDate?: string, refresh = false) => {
    setError(null);
    setLoading(true);
    if (refresh) {
      setIsRefreshing(true);
    }

    try {
      const [summaryData, dailyData] = await Promise.all([
        fetchSummary(targetDate),
        fetchDailyStats(),
      ]);
      setSummary(summaryData);
      setDailyStats(dailyData.data || []);
      setLastUpdated(new Date());
      if (!targetDate && summaryData.date) {
        setSelectedDate(summaryData.date);
      }
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load dashboard data."));
    } finally {
      setLoading(false);
      if (refresh) {
        setIsRefreshing(false);
      }
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    const init = async () => {
      try {
        const result = await getAvailableDates();
        if (cancelled) {
          return;
        }

        const dates = result.dates || [];
        setAvailableDates(dates);

        const initialDate = dates[0];
        if (initialDate) {
          setSelectedDate(initialDate);
          await loadDashboardData(initialDate, true);
          return;
        }
      } catch {
        if (cancelled) {
          return;
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

  return {
    summary,
    dailyStats,
    loading,
    error,
    selectedDate,
    availableDates,
    lastUpdated,
    isRefreshing,
    handleDateChange,
    handleRefresh,
  };
}
