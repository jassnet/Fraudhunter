"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { OverviewChart } from "@/components/overview-chart";
import { Activity, MousePointerClick, Target, AlertTriangle, ArrowUpRight, ArrowDownRight, RefreshCw, Play } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
            
            <div className="space-y-2">
              <p className="text-sm font-medium">解決方法:</p>
              <ol className="text-sm text-muted-foreground list-decimal list-inside space-y-2">
                <li>
                  プロジェクトルートで以下を実行:
                  <code className="ml-2 bg-muted px-2 py-1 rounded text-xs">python dev.py</code>
                </li>
                <li>
                  または、バックエンドのみ起動:
                  <code className="ml-2 bg-muted px-2 py-1 rounded text-xs">cd backend && python -m uvicorn fraud_checker.api:app --reload --app-dir ./src</code>
                </li>
              </ol>
            </div>

            <div className="text-sm text-muted-foreground border-t pt-4 mt-4">
              <p className="font-medium mb-2">チェックリスト:</p>
              <ul className="list-disc list-inside space-y-1">
                <li><code className="bg-muted px-1 rounded">.env</code> ファイルが設定されているか</li>
                <li><code className="bg-muted px-1 rounded">FRAUD_DB_PATH</code>、<code className="bg-muted px-1 rounded">ACS_*</code> 環境変数が設定されているか</li>
                <li>ポート 8000 が使用可能か</li>
              </ul>
            </div>

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
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
            <h2 className="text-3xl font-bold tracking-tight">ダッシュボード</h2>
            <p className="text-muted-foreground">
                {summary.date} 時点の集計データ
            </p>
        </div>
        <div className="flex items-center space-x-2">
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

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">概要</TabsTrigger>
          <TabsTrigger value="analytics" disabled>分析 (WIP)</TabsTrigger>
          <TabsTrigger value="reports" disabled>レポート (WIP)</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
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
                  <span className="ml-1">from yesterday</span>
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
                  <span className="ml-1">from yesterday</span>
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
                <p className="text-xs text-muted-foreground pt-1">
                  検知された高リスクIP
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">不正疑惑 (成果)</CardTitle>
                <AlertTriangle className="h-4 w-4 text-red-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary.stats.suspicious.conversion_based}</div>
                <p className="text-xs text-muted-foreground pt-1">
                  検知された高リスク成果IP
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-4">
              <CardHeader>
                <CardTitle>推移 (過去30日)</CardTitle>
              </CardHeader>
              <CardContent className="pl-2">
                <OverviewChart data={dailyStats} />
              </CardContent>
            </Card>
            <Card className="col-span-3">
              <CardHeader>
                <CardTitle>システム状況</CardTitle>
                <CardDescription>
                    監視対象の指標
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-8">
                    <div className="flex items-center">
                        <Activity className="h-9 w-9 text-primary bg-primary/10 p-2 rounded-full" />
                        <div className="ml-4 space-y-1">
                            <p className="text-sm font-medium leading-none">稼働中の媒体数</p>
                            <p className="text-sm text-muted-foreground">
                                {summary.stats.clicks.media_count} Media IDs
                            </p>
                        </div>
                        <div className="ml-auto font-medium">Active</div>
                    </div>
                    <div className="flex items-center">
                        <div className="ml-4 space-y-1">
                            <p className="text-sm font-medium leading-none">ユニークIP (Click)</p>
                            <p className="text-sm text-muted-foreground">
                                {summary.stats.clicks.unique_ips.toLocaleString()} IPs
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center">
                        <div className="ml-4 space-y-1">
                            <p className="text-sm font-medium leading-none">ユニークIP (CV)</p>
                            <p className="text-sm text-muted-foreground">
                                {summary.stats.conversions.unique_ips.toLocaleString()} IPs
                            </p>
                        </div>
                    </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      <RefreshDialog 
        open={showRefreshDialog} 
        onOpenChange={setShowRefreshDialog}
        onSuccess={handleRefresh}
      />
    </div>
  );
}
