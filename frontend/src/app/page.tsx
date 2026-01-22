"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { OverviewChart } from "@/components/overview-chart";
import { 
  Activity, 
  MousePointerClick, 
  Target, 
  AlertTriangle, 
  ArrowUpRight, 
  ArrowDownRight, 
  Play,
  TrendingUp,
  Shield,
  ExternalLink
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  fetchSummary,
  fetchDailyStats,
  DailyStatsItem,
  getAvailableDates,
  getErrorMessage,
  SummaryResponse,
} from "@/lib/api";
import { RefreshDialog } from "@/components/refresh-dialog";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";

export default function DashboardPage() {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStatsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showRefreshDialog, setShowRefreshDialog] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = useCallback(async (targetDate?: string) => {
    setError(null);
    try {
      const [summaryData, dailyData] = await Promise.all([
        fetchSummary(targetDate),
        fetchDailyStats()
      ]);
      
      setSummary(summaryData);
      setDailyStats(dailyData.data || []);
      setLastUpdated(new Date());
      
      // 日付を設定（初回のみ）
      if (!targetDate && summaryData.date) {
        setSelectedDate(summaryData.date);
      }
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
      const message = getErrorMessage(err, "データの取得に失敗しました。");
      setError(`${message} バックエンドが起動しているか確認してください。`);
    } finally {
      setLoading(false);
    }
  }, []);

  // 初期化: 日付一覧を取得し、最初の日付を選択
  useEffect(() => {
    const init = async () => {
      try {
        const result = await getAvailableDates();
        const dates = result.dates || [];
        setAvailableDates(dates);
        if (dates.length > 0) {
          // 日付があれば最初の日付を選択（useEffect[selectedDate]がfetchDataを呼ぶ）
          setSelectedDate(dates[0]);
        } else {
          // 日付がない場合は日付なしでデータ取得
          fetchData();
        }
      } catch (err) {
        console.error("Failed to load dates", err);
        // エラー時も日付なしでデータ取得を試みる
        fetchData();
      }
    };
    init();
  }, [fetchData]);

  // 日付が変わったらデータを再取得
  useEffect(() => {
    if (selectedDate) {
      fetchData(selectedDate);
    }
  }, [selectedDate, fetchData]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData(selectedDate);
    setRefreshing(false);
  }, [fetchData, selectedDate]);

  const handleDateChange = (date: string) => {
    setSelectedDate(date);
  };

  const calculateTrend = (current: number, prev: number) => {
    if (prev === 0) return current > 0 ? 100 : 0;
    return ((current - prev) / prev) * 100;
  };

  // 不正検知率の計算
  const getSuspiciousRate = () => {
    if (!summary) return { clickRate: 0, convRate: 0 };
    const clickRate = summary.stats.clicks.unique_ips > 0 
      ? (summary.stats.suspicious.click_based / summary.stats.clicks.unique_ips * 100) 
      : 0;
    const convRate = summary.stats.conversions.unique_ips > 0 
      ? (summary.stats.suspicious.conversion_based / summary.stats.conversions.unique_ips * 100) 
      : 0;
    return { clickRate, convRate };
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
  const suspiciousRates = getSuspiciousRate();

  // 直近7日間の不正検知数の合計
  const recentSuspicious = dailyStats.slice(-7).reduce((acc, d) => ({
    clicks: acc.clicks + (d.suspicious_clicks || 0),
    conversions: acc.conversions + (d.suspicious_conversions || 0)
  }), { clicks: 0, conversions: 0 });

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      {/* ヘッダー：タイトル、日付選択、更新ボタン */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">ダッシュボード</h2>
          <p className="text-muted-foreground">
            {summary.date} の集計データ
          </p>
        </div>
        
        {/* 日付選択と更新コントロール */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <DateQuickSelect
            value={selectedDate}
            onChange={handleDateChange}
            availableDates={availableDates}
            showQuickButtons={true}
          />
          
          <div className="flex items-center gap-2">
            <LastUpdated
              lastUpdated={lastUpdated}
              onRefresh={handleRefresh}
              isRefreshing={refreshing}
              showAutoRefresh={true}
            />
            
            <Button size="sm" onClick={() => setShowRefreshDialog(true)} className="h-8">
              <Play className="mr-1.5 h-3.5 w-3.5" />
              データ取込
            </Button>
          </div>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">概要</TabsTrigger>
          <TabsTrigger value="suspicious">不正検知</TabsTrigger>
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
                  <span className="ml-1">前日比</span>
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
                  <span className="ml-1">前日比</span>
                </p>
              </CardContent>
            </Card>

            {/* 不正クリック検知 - クリック可能 */}
            <Link href="/suspicious/clicks">
              <Card className="cursor-pointer transition-all hover:shadow-md hover:border-yellow-500/50 group">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    不正疑惑 (クリック)
                    <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </CardTitle>
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-yellow-600">{summary.stats.suspicious.click_based}</div>
                  <p className="text-xs text-muted-foreground pt-1">
                    検知率: {suspiciousRates.clickRate.toFixed(2)}%
                  </p>
                </CardContent>
              </Card>
            </Link>

            {/* 不正成果検知 - クリック可能 */}
            <Link href="/suspicious/conversions">
              <Card className="cursor-pointer transition-all hover:shadow-md hover:border-red-500/50 group">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    不正疑惑 (成果)
                    <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </CardTitle>
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-600">{summary.stats.suspicious.conversion_based}</div>
                  <p className="text-xs text-muted-foreground pt-1">
                    検知率: {suspiciousRates.convRate.toFixed(2)}%
                  </p>
                </CardContent>
              </Card>
            </Link>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-4">
              <CardHeader>
                <CardTitle>推移 (過去30日)</CardTitle>
                <CardDescription>クリック数・成果数・不正検知数の日次推移</CardDescription>
              </CardHeader>
              <CardContent className="pl-2">
                <OverviewChart data={dailyStats} />
              </CardContent>
            </Card>
            <Card className="col-span-3">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  システム状況
                </CardTitle>
                <CardDescription>
                    監視対象の指標
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                    <div className="flex items-center">
                        <Activity className="h-9 w-9 text-primary bg-primary/10 p-2 rounded-full" />
                        <div className="ml-4 space-y-1">
                            <p className="text-sm font-medium leading-none">稼働中の媒体数</p>
                            <p className="text-sm text-muted-foreground">
                                {summary.stats.clicks.media_count} Media IDs
                            </p>
                        </div>
                        <Badge variant="outline" className="ml-auto">Active</Badge>
                    </div>
                    <div className="flex items-center">
                        <MousePointerClick className="h-9 w-9 text-blue-500 bg-blue-500/10 p-2 rounded-full" />
                        <div className="ml-4 space-y-1">
                            <p className="text-sm font-medium leading-none">ユニークIP (Click)</p>
                            <p className="text-sm text-muted-foreground">
                                {summary.stats.clicks.unique_ips.toLocaleString()} IPs
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center">
                        <Target className="h-9 w-9 text-green-500 bg-green-500/10 p-2 rounded-full" />
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

        {/* 不正検知タブ */}
        <TabsContent value="suspicious" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* 不正クリック統計 */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-yellow-500" />
                      不正クリック検知
                    </CardTitle>
                    <CardDescription>今日の不正疑惑クリック</CardDescription>
                  </div>
                  <Link href="/suspicious/clicks">
                    <Button variant="outline" size="sm">
                      詳細を見る
                      <ExternalLink className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-yellow-600">
                      {summary.stats.suspicious.click_based}
                    </span>
                    <span className="text-muted-foreground">件検知</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">検知率</span>
                      <span className="font-medium">{suspiciousRates.clickRate.toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">過去7日間合計</span>
                      <span className="font-medium">{recentSuspicious.clicks}件</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 不正成果統計 */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-red-500" />
                      不正成果検知
                    </CardTitle>
                    <CardDescription>今日の不正疑惑成果</CardDescription>
                  </div>
                  <Link href="/suspicious/conversions">
                    <Button variant="outline" size="sm">
                      詳細を見る
                      <ExternalLink className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-red-600">
                      {summary.stats.suspicious.conversion_based}
                    </span>
                    <span className="text-muted-foreground">件検知</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">検知率</span>
                      <span className="font-medium">{suspiciousRates.convRate.toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">過去7日間合計</span>
                      <span className="font-medium">{recentSuspicious.conversions}件</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 不正検知推移グラフ */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                不正検知推移 (過去30日)
              </CardTitle>
              <CardDescription>
                日別の不正検知数の推移
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <SuspiciousChart data={dailyStats} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <RefreshDialog 
        open={showRefreshDialog} 
        onOpenChange={setShowRefreshDialog}
        onSuccess={handleRefresh}
        initialDate={selectedDate}
      />
    </div>
  );
}

// 不正検知専用チャート
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from "recharts";

function SuspiciousChart({ data }: { data: DailyStatsItem[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <XAxis
          dataKey="date"
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => {
            const date = new Date(value);
            return `${date.getMonth() + 1}/${date.getDate()}`;
          }}
        />
        <YAxis
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          contentStyle={{ 
            backgroundColor: 'hsl(var(--background))', 
            borderColor: 'hsl(var(--border))',
            borderRadius: '8px'
          }}
          labelStyle={{ color: 'hsl(var(--foreground))' }}
          labelFormatter={(value) => {
            const date = new Date(value);
            return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`;
          }}
        />
        <Legend />
        <Bar
          dataKey="suspicious_clicks"
          name="不正クリック"
          fill="hsl(45, 93%, 47%)"
          radius={[4, 4, 0, 0]}
        />
        <Bar
          dataKey="suspicious_conversions"
          name="不正成果"
          fill="hsl(0, 84%, 60%)"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
