"use client";

import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Search,
  Download,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Loader2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ArrowUpDown,
  X,
  AlertCircle,
  Info,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  SuspiciousItem,
  SuspiciousResponse,
  getAvailableDates,
} from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";

type MetricKey = "total_clicks" | "total_conversions";
type SuspiciousFetcher = (
  date?: string,
  limit?: number,
  offset?: number,
  search?: string
) => Promise<SuspiciousResponse>;

type SortKey = "risk" | "count" | "media" | "program";
type SortOrder = "asc" | "desc";

interface SuspiciousListPageProps {
  title: string;
  description: string;
  ipLabel: string;
  countLabel: string;
  csvPrefix: string;
  fetcher: SuspiciousFetcher;
  metricKey: MetricKey;
}

const PAGE_SIZE = 50;
const SEARCH_DEBOUNCE_MS = 500;
const CSV_MAX_ROWS = 10000;

// リスクレベルの色とアイコン
const RISK_CONFIG = {
  high: {
    color: "bg-red-500/10 text-red-600 border-red-500/30",
    bgColor: "bg-red-50 dark:bg-red-950/20",
    icon: AlertCircle,
    label: "高リスク",
  },
  medium: {
    color: "bg-yellow-500/10 text-yellow-600 border-yellow-500/30",
    bgColor: "bg-yellow-50 dark:bg-yellow-950/20",
    icon: AlertTriangle,
    label: "中リスク",
  },
  low: {
    color: "bg-blue-500/10 text-blue-600 border-blue-500/30",
    bgColor: "bg-blue-50 dark:bg-blue-950/20",
    icon: Info,
    label: "低リスク",
  },
};

export default function SuspiciousListPage({
  title,
  description,
  ipLabel,
  countLabel,
  csvPrefix,
  fetcher,
  metricKey,
}: SuspiciousListPageProps) {
  const [data, setData] = useState<SuspiciousItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [date, setDate] = useState<string>("");
  const [csvWarningOpen, setCsvWarningOpen] = useState(false);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [exporting, setExporting] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  // 新機能: 展開行の管理
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  
  // 新機能: ソート
  const [sortKey, setSortKey] = useState<SortKey>("risk");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  // 新機能: フィルタ
  const [riskFilter, setRiskFilter] = useState<string>("all");

  // 検索のデバウンス処理
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setPage(1);
    }, SEARCH_DEBOUNCE_MS);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [searchTerm]);

  const fetchData = useCallback(
    async (targetDate: string | undefined, pageNum: number, search?: string) => {
      setLoading(true);
      setError(null);
      try {
        const offset = (pageNum - 1) * PAGE_SIZE;
        const json = await fetcher(targetDate || undefined, PAGE_SIZE, offset, search || undefined);
        if (json.data) {
          setData(json.data);
          setTotal(json.total);
          setLastUpdated(new Date());
          if (!targetDate && json.date) setDate(json.date);
        }
      } catch (err) {
        console.error(err);
        setError("データの取得に失敗しました");
      } finally {
        setLoading(false);
      }
    },
    [fetcher]
  );

  const loadDates = useCallback(async () => {
    try {
      const result = await getAvailableDates();
      const dates = result.dates || [];
      setAvailableDates(dates);
      if (dates.length > 0) {
        setDate((prev) => prev || dates[0]);
      }
    } catch (err) {
      console.error("Failed to load dates", err);
    }
  }, []);

  useEffect(() => {
    loadDates();
  }, [loadDates]);

  useEffect(() => {
    if (date) {
      fetchData(date, page, debouncedSearch);
    }
  }, [date, page, debouncedSearch, fetchData]);

  const handleRefresh = useCallback(async () => {
    await fetchData(date, page, debouncedSearch);
  }, [fetchData, date, page, debouncedSearch]);

  const handleDateChange = (newDate: string) => {
    setPage(1);
    setDate(newDate);
  };

  // ソートとフィルタを適用したデータ
  const processedData = useCallback(() => {
    let filtered = [...data];

    // リスクフィルタ
    if (riskFilter !== "all") {
      filtered = filtered.filter((item) => item.risk_level === riskFilter);
    }

    // ソート
    filtered.sort((a, b) => {
      let aVal: number, bVal: number;
      switch (sortKey) {
        case "risk":
          aVal = a.risk_score || 0;
          bVal = b.risk_score || 0;
          break;
        case "count":
          aVal = a[metricKey] || 0;
          bVal = b[metricKey] || 0;
          break;
        case "media":
          aVal = a.media_count;
          bVal = b.media_count;
          break;
        case "program":
          aVal = a.program_count;
          bVal = b.program_count;
          break;
        default:
          aVal = 0;
          bVal = 0;
      }
      return sortOrder === "desc" ? bVal - aVal : aVal - bVal;
    });

    return filtered;
  }, [data, riskFilter, sortKey, sortOrder, metricKey]);

  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;

  const handlePageChange = (newPage: number) => {
    const nextPage = Math.min(Math.max(newPage, 1), totalPages);
    setPage(nextPage);
  };

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === "desc" ? "asc" : "desc");
    } else {
      setSortKey(key);
      setSortOrder("desc");
    }
  };

  const toggleRowExpand = (id: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleExportClick = () => {
    if (total === 0) return;
    if (total > CSV_MAX_ROWS) {
      setCsvWarningOpen(true);
    } else {
      exportCSV();
    }
  };

  const exportCSV = async () => {
    if (total === 0) return;
    setCsvWarningOpen(false);
    setExporting(true);

    try {
      const allData = await fetcher(date || undefined, CSV_MAX_ROWS, 0, debouncedSearch || undefined);
      const items = allData.data || [];
      const exportedCount = items.length;

      if (items.length === 0) {
        setExporting(false);
        return;
      }

      const headers = [
        "リスクレベル",
        ipLabel,
        "User Agent",
        countLabel,
        ...(metricKey === "total_conversions" ? ["最短経過時間(秒)", "最長経過時間(秒)"] : []),
        "媒体数",
        "媒体名",
        "案件数",
        "案件名",
        "判定理由",
      ];

      const rows = items.map((item) => [
        item.risk_label || "-",
        item.ipaddress,
        `"${item.useragent.replace(/"/g, '""')}"`,
        item[metricKey] ?? 0,
        ...(metricKey === "total_conversions" ? [
          item.min_click_to_conv_seconds ?? "",
          item.max_click_to_conv_seconds ?? ""
        ] : []),
        item.media_count,
        `"${(item.media_names || []).join(", ")}"`,
        item.program_count,
        `"${(item.program_names || []).join(", ")}"`,
        `"${(item.reasons_formatted || item.reasons || []).join(", ")}"`,
      ]);

      const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
      const bom = "\uFEFF";
      const blob = new Blob([bom + csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${csvPrefix}_${date}${debouncedSearch ? `_${debouncedSearch}` : ""}.csv`;
      a.click();
      URL.revokeObjectURL(url);

      if (total > exportedCount) {
        setError(`${exportedCount.toLocaleString()}件を出力しました（全${total.toLocaleString()}件中）`);
        setTimeout(() => setError(null), 5000);
      }
    } catch (err) {
      console.error("CSV export failed", err);
      setError("CSV出力に失敗しました");
    } finally {
      setExporting(false);
    }
  };

  // 統計サマリーの計算
  const stats = {
    high: data.filter((d) => d.risk_level === "high").length,
    medium: data.filter((d) => d.risk_level === "medium").length,
    low: data.filter((d) => d.risk_level === "low").length,
  };

  const sortIcon = (key: SortKey) => {
    if (sortKey !== key) return <ArrowUpDown className="h-4 w-4 ml-1 opacity-50" />;
    return sortOrder === "desc" ? (
      <ChevronDown className="h-4 w-4 ml-1" />
    ) : (
      <ChevronUp className="h-4 w-4 ml-1" />
    );
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      {/* ヘッダー */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
          <p className="text-muted-foreground">{description}</p>
        </div>
        
        {/* 日付選択と更新コントロール */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <DateQuickSelect
            value={date}
            onChange={handleDateChange}
            availableDates={availableDates}
            showQuickButtons={true}
          />
          
          <div className="flex items-center gap-2">
            <LastUpdated
              lastUpdated={lastUpdated}
              onRefresh={handleRefresh}
              isRefreshing={loading}
              showAutoRefresh={true}
            />
            
            <Button size="sm" onClick={handleExportClick} disabled={total === 0 || exporting} className="h-8">
              {exporting ? (
                <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
              ) : (
                <Download className="mr-1.5 h-3.5 w-3.5" />
              )}
              {exporting ? "出力中..." : "CSV"}
            </Button>
          </div>
        </div>
      </div>

      {/* リスク別サマリーカード */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">総検知数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{total.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card 
          className={`cursor-pointer transition-all ${riskFilter === "high" ? "ring-2 ring-red-500" : "hover:shadow-md"}`}
          onClick={() => setRiskFilter(riskFilter === "high" ? "all" : "high")}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-500" />
              高リスク
            </CardTitle>
            <CardDescription className="text-xs">クリックでフィルタ切替</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.high}</div>
          </CardContent>
        </Card>
        <Card 
          className={`cursor-pointer transition-all ${riskFilter === "medium" ? "ring-2 ring-yellow-500" : "hover:shadow-md"}`}
          onClick={() => setRiskFilter(riskFilter === "medium" ? "all" : "medium")}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              中リスク
            </CardTitle>
            <CardDescription className="text-xs">クリックでフィルタ切替</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.medium}</div>
          </CardContent>
        </Card>
        <Card 
          className={`cursor-pointer transition-all ${riskFilter === "low" ? "ring-2 ring-blue-500" : "hover:shadow-md"}`}
          onClick={() => setRiskFilter(riskFilter === "low" ? "all" : "low")}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Info className="h-4 w-4 text-blue-500" />
              低リスク
            </CardTitle>
            <CardDescription className="text-xs">クリックでフィルタ切替</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.low}</div>
          </CardContent>
        </Card>
      </div>

      {/* CSV出力警告ダイアログ */}
      <Dialog open={csvWarningOpen} onOpenChange={setCsvWarningOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              CSV出力の制限
            </DialogTitle>
            <DialogDescription className="pt-2">
              対象データが{total.toLocaleString()}件あります。
              CSV出力は最大{CSV_MAX_ROWS.toLocaleString()}件までに制限されています。
              <br /><br />
              検索条件を追加して件数を絞り込むか、このまま上位{CSV_MAX_ROWS.toLocaleString()}件を出力してください。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setCsvWarningOpen(false)}>
              キャンセル
            </Button>
            <Button onClick={exportCSV}>
              上位{CSV_MAX_ROWS.toLocaleString()}件を出力
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* メインテーブルカード */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>検知リスト ({date || "データなし"})</CardTitle>
              <CardDescription>
                {riskFilter !== "all" && (
                  <Badge variant="secondary" className="mr-2">
                    {RISK_CONFIG[riskFilter as keyof typeof RISK_CONFIG]?.label}でフィルタ中
                    <button onClick={() => setRiskFilter("all")} className="ml-1">
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                )}
                {processedData().length}件表示 / 全{total}件
                <span className="ml-2 text-xs text-muted-foreground">(表示中のデータにフィルタを適用)</span>
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative w-full max-w-sm">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="IP・UA・媒体名・案件名で検索..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 w-[300px]"
                />
                {searchTerm && searchTerm !== debouncedSearch && (
                  <Loader2 className="absolute right-2.5 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />
                )}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="text-center py-8 text-red-500">{error}</div>
          ) : loading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[40px]"></TableHead>
                      <TableHead 
                        className="w-[100px] cursor-pointer hover:bg-muted/50"
                        onClick={() => toggleSort("risk")}
                      >
                        <div className="flex items-center">
                          リスク
                          {sortIcon("risk")}
                        </div>
                      </TableHead>
                      <TableHead className="w-[130px]">{ipLabel}</TableHead>
                      <TableHead 
                        className="text-right cursor-pointer hover:bg-muted/50"
                        onClick={() => toggleSort("count")}
                      >
                        <div className="flex items-center justify-end">
                          {countLabel}
                          {sortIcon("count")}
                        </div>
                      </TableHead>
                      {metricKey === "total_conversions" && (
                        <TableHead className="text-center">経過時間</TableHead>
                      )}
                      <TableHead 
                        className="text-center cursor-pointer hover:bg-muted/50"
                        onClick={() => toggleSort("media")}
                      >
                        <div className="flex items-center justify-center">
                          媒体
                          {sortIcon("media")}
                        </div>
                      </TableHead>
                      <TableHead 
                        className="text-center cursor-pointer hover:bg-muted/50"
                        onClick={() => toggleSort("program")}
                      >
                        <div className="flex items-center justify-center">
                          案件
                          {sortIcon("program")}
                        </div>
                      </TableHead>
                      <TableHead>判定理由</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {processedData().length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={metricKey === "total_conversions" ? 8 : 7} className="h-24 text-center">
                          データが見つかりません
                        </TableCell>
                      </TableRow>
                    ) : (
                      processedData().map((item, i) => {
                        const rowId = `${item.ipaddress}-${i}`;
                        const isExpanded = expandedRows.has(rowId);
                        const riskConfig = RISK_CONFIG[item.risk_level || "low"];
                        const RiskIcon = riskConfig.icon;

                        return (
                          <Fragment key={rowId}>
                            <TableRow className={`${isExpanded ? riskConfig.bgColor : ""}`}>
                              <TableCell>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-8 w-8 p-0"
                                  onClick={() => toggleRowExpand(rowId)}
                                  aria-expanded={isExpanded}
                                  aria-label={isExpanded ? "閉じる" : "開く"}
                                >
                                  {isExpanded ? (
                                    <ChevronUp className="h-4 w-4" />
                                  ) : (
                                    <ChevronDown className="h-4 w-4" />
                                  )}
                                </Button>
                              </TableCell>
                              <TableCell>
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger>
                                      <Badge 
                                        variant="outline" 
                                        className={`${riskConfig.color} flex items-center gap-1`}
                                      >
                                        <RiskIcon className="h-3 w-3" />
                                        {riskConfig.label}
                                      </Badge>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      <p>リスクスコア: {item.risk_score}</p>
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              </TableCell>
                              <TableCell className="font-mono text-xs">
                                {item.ipaddress}
                              </TableCell>
                              <TableCell className="text-right font-bold text-lg">
                                {item[metricKey] ?? 0}
                              </TableCell>
                              {metricKey === "total_conversions" && (
                                <TableCell className="text-center text-xs font-mono">
                                  {item.min_click_to_conv_seconds !== null &&
                                  item.min_click_to_conv_seconds !== undefined ? (
                                    <span>
                                      {Math.round(item.min_click_to_conv_seconds)}s
                                      {item.max_click_to_conv_seconds !== null &&
                                      item.max_click_to_conv_seconds !== undefined &&
                                      item.max_click_to_conv_seconds !== item.min_click_to_conv_seconds
                                        ? ` - ${Math.round(item.max_click_to_conv_seconds)}s`
                                        : ""}
                                    </span>
                                  ) : (
                                    <span className="text-muted-foreground">-</span>
                                  )}
                                </TableCell>
                              )}
                              <TableCell className="text-center">
                                <div className="text-sm">
                                  <span className="font-bold">{item.media_count}</span>
                                  {item.media_names && item.media_names.length > 0 && (
                                    <div
                                      className="text-xs text-muted-foreground truncate max-w-[100px]"
                                      title={item.media_names.join(", ")}
                                    >
                                      {item.media_names[0]}
                                      {item.media_names.length > 1 && ` +${item.media_names.length - 1}`}
                                    </div>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell className="text-center">
                                <div className="text-sm">
                                  <span className="font-bold">{item.program_count}</span>
                                  {item.program_names && item.program_names.length > 0 && (
                                    <div
                                      className="text-xs text-muted-foreground truncate max-w-[100px]"
                                      title={item.program_names.join(", ")}
                                    >
                                      {item.program_names[0]}
                                      {item.program_names.length > 1 && ` +${item.program_names.length - 1}`}
                                    </div>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="flex flex-wrap gap-1 max-w-[300px]">
                                  {(item.reasons_formatted || item.reasons || []).slice(0, 2).map((reason, idx) => (
                                    <Badge key={idx} variant="secondary" className="text-xs">
                                      {reason}
                                    </Badge>
                                  ))}
                                  {(item.reasons_formatted || item.reasons || []).length > 2 && (
                                    <Badge variant="outline" className="text-xs">
                                      +{(item.reasons_formatted || item.reasons || []).length - 2}
                                    </Badge>
                                  )}
                                </div>
                              </TableCell>
                            </TableRow>
                            {isExpanded && (
                              <TableRow className={riskConfig.bgColor}>
                                <TableCell colSpan={metricKey === "total_conversions" ? 8 : 7} className="p-0">
                                  <div className="p-4 space-y-4">
                                    {/* User Agent */}
                                    <div>
                                      <label className="text-xs font-medium text-muted-foreground">User Agent</label>
                                      <p className="text-xs break-all bg-muted/50 p-2 rounded mt-1 font-mono">
                                        {item.useragent}
                                      </p>
                                    </div>

                                    {/* 判定理由 */}
                                    <div>
                                      <label className="text-xs font-medium text-muted-foreground">判定理由</label>
                                      <div className="flex flex-wrap gap-2 mt-1">
                                        {(item.reasons_formatted || item.reasons || []).map((r, idx) => (
                                          <Badge key={idx} variant="destructive">
                                            {r}
                                          </Badge>
                                        ))}
                                      </div>
                                    </div>

                                    {/* 詳細テーブル */}
                                    {item.details && item.details.length > 0 && (
                                      <div>
                                        <label className="text-xs font-medium text-muted-foreground">関連媒体・案件</label>
                                        <div className="mt-1 rounded border">
                                          <Table>
                                            <TableHeader>
                                              <TableRow>
                                                <TableHead className="text-xs">媒体名</TableHead>
                                                <TableHead className="text-xs">案件名</TableHead>
                                                <TableHead className="text-xs text-right">{countLabel}</TableHead>
                                              </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                              {item.details.map((d, idx) => (
                                                <TableRow key={`${d.media_id}-${d.program_id}-${idx}`}>
                                                  <TableCell className="text-xs py-2">{d.media_name}</TableCell>
                                                  <TableCell className="text-xs py-2">{d.program_name}</TableCell>
                                                  <TableCell className="text-xs text-right py-2 font-medium">
                                                    {metricKey === "total_clicks" ? d.click_count : d.conversion_count}
                                                  </TableCell>
                                                </TableRow>
                                              ))}
                                            </TableBody>
                                          </Table>
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                </TableCell>
                              </TableRow>
                            )}
                          </Fragment>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </div>

              {/* ページネーション */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-2 py-4">
                  <div className="text-sm text-muted-foreground">
                    {(page - 1) * PAGE_SIZE + 1} - {Math.min(page * PAGE_SIZE, total)} / {total}件
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(1)}
                      disabled={page === 1 || loading}
                    >
                      <ChevronsLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(page - 1)}
                      disabled={page === 1 || loading}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm">
                      {page} / {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(page + 1)}
                      disabled={page === totalPages || loading}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(totalPages)}
                      disabled={page === totalPages || loading}
                    >
                      <ChevronsRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
