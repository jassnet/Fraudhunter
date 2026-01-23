"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchDailyStats,
  fetchSummary,
  getAvailableDates,
  getErrorMessage,
  DailyStatsItem,
  SummaryResponse,
} from "@/lib/api";
import { OverviewChart } from "@/components/overview-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";

export default function DashboardPage() {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStatsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = useCallback(async (targetDate?: string) => {
    setError(null);
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
      const message = getErrorMessage(err, "Failed to load dashboard data.");
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      try {
        const result = await getAvailableDates();
        const dates = result.dates || [];
        setAvailableDates(dates);
        if (dates.length > 0) {
          setSelectedDate(dates[0]);
        } else {
          fetchData();
        }
      } catch {
        fetchData();
      }
    };
    init();
  }, [fetchData]);

  useEffect(() => {
    if (selectedDate) {
      fetchData(selectedDate);
    }
  }, [selectedDate, fetchData]);

  const handleRefresh = useCallback(async () => {
    await fetchData(selectedDate);
  }, [fetchData, selectedDate]);

  if (loading) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <Skeleton className="h-8 w-[200px]" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-[120px] rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-[400px] rounded-xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">{error}</p>
            <Button onClick={handleRefresh}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!summary) {
    return <div className="p-8">No data available.</div>;
  }

  return (
    <div className="flex-1 space-y-6 p-6 sm:p-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Date: {summary.date}</p>
        </div>

        <div className="w-full lg:w-auto">
          <div className="flex flex-col gap-3 rounded-xl border bg-card/60 p-3 sm:p-4 lg:flex-row lg:items-center lg:gap-4">
            <DateQuickSelect
              value={selectedDate}
              onChange={setSelectedDate}
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
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              Total Clicks
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-semibold tabular-nums">
              {summary.stats.clicks.total.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              Total Conversions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-semibold tabular-nums">
              {summary.stats.conversions.total.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Link href="/suspicious/clicks">
          <Card className="group cursor-pointer border-l-4 border-yellow-500/60 transition-shadow hover:shadow-md">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground">
                Suspicious Clicks
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="text-3xl font-semibold tabular-nums text-yellow-600">
                {summary.stats.suspicious.click_based}
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/suspicious/conversions">
          <Card className="group cursor-pointer border-l-4 border-red-500/60 transition-shadow hover:shadow-md">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground">
                Suspicious Conversions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="text-3xl font-semibold tabular-nums text-red-600">
                {summary.stats.suspicious.conversion_based}
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Last 30 days</CardTitle>
        </CardHeader>
        <CardContent className="pl-2 pt-2">
          <OverviewChart data={dailyStats} />
        </CardContent>
      </Card>
    </div>
  );
}
