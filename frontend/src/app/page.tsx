"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { OverviewChart } from "@/components/overview-chart";
import { Activity, MousePointerClick, Target, AlertTriangle, ArrowUpRight, ArrowDownRight, RefreshCw, Play } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { fetchSummary, fetchDailyStats } from "@/lib/api";
import { RefreshDialog } from "@/components/refresh-dialog";

interface SummaryData {
  date: string;
  stats: {
    clicks: {
      total: number;
      unique_ips: number;
      media_count: number;
      prev_total: number;
    };
    conversions: {
      total: number;
      unique_ips: number;
      prev_total: number;
    };
    suspicious: {
      click_based: number;
      conversion_based: number;
    };
  };
}

interface DailyStats {
  date: string;
  clicks: number;
  conversions: number;
}

const getYesterdayDateString = () => {
  const date = new Date();
  date.setDate(date.getDate() - 1);
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export default function DashboardPage() {
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showRefreshDialog, setShowRefreshDialog] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const targetDate = getYesterdayDateString();

  const fetchData = async () => {
    setError(null);
    try {
      const [summaryData, dailyData] = await Promise.all([
        fetchSummary(targetDate),
        fetchDailyStats()
      ]);
      
      setSummary(summaryData);
      const filteredDailyStats = (dailyData.data || []).filter(
        (item: DailyStats) => item.date <= targetDate
      );
      setDailyStats(filteredDailyStats);
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
      setError("データの取得に失敗しました。バックエンドが起動しているか確認してください。");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const calculateTrend = (current: number, prev: number) => {
    if (prev === 0) return current > 0 ? 100 : 0;
    return ((current - prev) / prev) * 100;
  };

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
            <CardTitle className="text-destructive">接続エラー</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">{error}</p>
            
            <Button onClick={handleRefresh}>
              <RefreshCw className="mr-2 h-4 w-4" />
              再試行
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!summary) return <div className="p-8">データが見つかりません</div>;

  const clickTrend = calculateTrend(summary.stats.clicks.total, summary.stats.clicks.prev_total);
  const conversionTrend = calculateTrend(summary.stats.conversions.total, summary.stats.conversions.prev_total);

  return (
    <div className="flex flex-col h-full space-y-4 p-8 pt-6 overflow-hidden">
      <div className="flex items-center justify-between space-y-2 shrink-0">
        <div className="flex items-center space-x-2 ml-auto">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            更新
          </Button>
          <Button size="sm" onClick={() => setShowRefreshDialog(true)}>
            <Play className="mr-2 h-4 w-4" />
            データ取込
          </Button>
        </div>
      </div>

      <div className="space-y-4 flex-1 flex flex-col min-h-0">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 shrink-0">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">総クリック数</CardTitle>
                <MousePointerClick className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.stats.clicks.total.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground flex items-center pt-1">
                  {clickTrend >= 0 ? <ArrowUpRight className="h-3 w-3 text-green-500 mr-1" /> : <ArrowDownRight className="h-3 w-3 text-red-500 mr-1" />}
                  <span className={clickTrend >= 0 ? "text-green-500" : "text-red-500"}>{Math.abs(clickTrend).toFixed(1)}%</span>
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">総成果数</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.stats.conversions.total.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground flex items-center pt-1">
                  {conversionTrend >= 0 ? <ArrowUpRight className="h-3 w-3 text-green-500 mr-1" /> : <ArrowDownRight className="h-3 w-3 text-red-500 mr-1" />}
                  <span className={conversionTrend >= 0 ? "text-green-500" : "text-red-500"}>{Math.abs(conversionTrend).toFixed(1)}%</span>
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">不正疑惑 (クリック)</CardTitle>
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.stats.suspicious.click_based}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">不正疑惑 (成果)</CardTitle>
                <AlertTriangle className="h-4 w-4 text-red-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.stats.suspicious.conversion_based}</div>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7 flex-1 min-h-0">
            <Card className="col-span-7 flex flex-col">
              <CardHeader className="shrink-0">
                <CardTitle>推移 (過去30日)</CardTitle>
              </CardHeader>
              <CardContent className="pl-2 flex-1 min-h-0">
                <OverviewChart data={dailyStats} />
              </CardContent>
            </Card>
          </div>
      </div>

      <RefreshDialog 
        open={showRefreshDialog} 
        onOpenChange={setShowRefreshDialog}
        onSuccess={handleRefresh}
      />
    </div>
  );
}
