"use client";

import { Fragment, useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
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
import { Label } from "@/components/ui/label";
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
  getErrorMessage,
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
import { Breadcrumbs } from "@/components/breadcrumbs";
import { cn } from "@/lib/utils";
import { useNotifications } from "@/components/notification-center";

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
const EXPORT_PAGE_SIZE = 1000;

type HumanReasonPattern = {
  regex: RegExp;
  format: (match: RegExpMatchArray) => string;
};

// 判定理由をフロント側でより読みやすい表現に整形する
const HUMAN_REASON_PATTERNS: HumanReasonPattern[] = [
  {
    regex: /^total_clicks\s*>=\s*(\d+)/i,
    format: ([, threshold]) => `クリックが多すぎます（${threshold}回以上）`,
  },
  {
    regex: /^conversion_count\s*>=\s*(\d+)/i,
    format: ([, threshold]) => `成果が異常に多く発生しています（${threshold}件以上）`,
  },
  {
    regex: /^media_count\s*>=\s*(\d+)/i,
    format: ([, threshold]) =>
      `同じIP/UAから複数のメディアへアクセス（${threshold}メディア以上）`,
  },
  {
    regex: /^program_count\s*>=\s*(\d+)/i,
    format: ([, threshold]) =>
      `同じIP/UAで複数案件を閲覧（${threshold}案件以上）`,
  },
  {
    regex: /^burst:\s*(\d+)\s*clicks\s*in\s*(\d+)s.*<=\s*(\d+)s/i,
    format: ([, count, duration, window]) =>
      `短時間にクリックが集中（${duration}秒で${count}回、目安${window}秒以内）`,
  },
  {
    regex: /^burst:\s*(\d+)\s*conversions\s*in\s*(\d+)s.*<=\s*(\d+)s/i,
    format: ([, count, duration, window]) =>
      `短時間に成果が集中（${duration}秒で${count}件、目安${window}秒以内）`,
  },
  {
    regex: /^click_to_conversion_seconds\s*<=\s*(\d+)s.*min=(\d+)s/i,
    format: ([, threshold, actual]) =>
      `クリックから成果までが早すぎます（最短${actual}秒、基準${threshold}秒以内）`,
  },
  {
    regex: /^click_to_conversion_seconds\s*>=\s*(\d+)s.*max=(\d+)s/i,
    format: ([, threshold, actual]) =>
      `クリックから成果までが遅すぎます（最長${actual}秒、基準${threshold}秒以上）`,
  },
  {
    regex: /^click_to_conversion_seconds\s*<=\s*(\d+)s/i,
    format: ([, threshold]) => `クリックから成果までの時間が極端に短い（基準${threshold}秒以内）`,
  },
  {
    regex: /^click_to_conversion_seconds\s*>=\s*(\d+)s/i,
    format: ([, threshold]) => `クリックから成果までの時間が極端に長い（基準${threshold}秒以上）`,
  },
];

const humanizeReasons = (reasons?: string[]) => {
  if (!reasons) return [];
  return reasons.map((reason) => {
    for (const pattern of HUMAN_REASON_PATTERNS) {
      const match = reason.match(pattern.regex);
      if (match) return pattern.format(match);
    }
    return reason;
  });
};

const readableReasonsFor = (item: SuspiciousItem) => {
  const source = item.reasons?.length ? item.reasons : item.reasons_formatted || [];
  const mapped = humanizeReasons(source);
  // 重複を除去して表示をすっきりさせる
  return Array.from(new Set(mapped.length ? mapped : source));
};

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
  const [isFetching, setIsFetching] = useState(false);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const [date, setDate] = useState<string>("");
  const [csvWarningOpen, setCsvWarningOpen] = useState(false);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [dateError, setDateError] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [exporting, setExporting] = useState(false);
  const [exportStage, setExportStage] = useState<"idle" | "fetching" | "building">("idle");
  const [exportProgress, setExportProgress] = useState<{ current: number; total: number } | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const searchId = useId();
  const { notify } = useNotifications();
  const storageKey = useMemo(() => `fraudchecker:suspicious:${metricKey}`, [metricKey]);
  const [hasRestoredFilters, setHasRestoredFilters] = useState(false);

  // 新機能: 展開行の管理
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  
  // 新機能: ソート
  const [sortKey, setSortKey] = useState<SortKey>("risk");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  // 新機能: フィルタ
  const [riskFilter, setRiskFilter] = useState<string>("all");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) {
      setHasRestoredFilters(true);
      return;
    }
    try {
      const parsed = JSON.parse(raw) as Partial<{
        date: string;
        searchTerm: string;
        sortKey: SortKey;
        sortOrder: SortOrder;
        riskFilter: string;
      }>;

      if (parsed.date) setDate(parsed.date);
      if (parsed.searchTerm !== undefined) {
        setSearchTerm(parsed.searchTerm);
        setDebouncedSearch(parsed.searchTerm);
      }
      if (parsed.sortKey && ["risk", "count", "media", "program"].includes(parsed.sortKey)) {
        setSortKey(parsed.sortKey);
      }
      if (parsed.sortOrder && ["asc", "desc"].includes(parsed.sortOrder)) {
        setSortOrder(parsed.sortOrder);
      }
      if (parsed.riskFilter && ["all", "high", "medium", "low"].includes(parsed.riskFilter)) {
        setRiskFilter(parsed.riskFilter);
      }
    } catch (err) {
      console.warn("Failed to restore filters", err);
    } finally {
      setHasRestoredFilters(true);
    }
  }, [storageKey]);

  useEffect(() => {
    if (!hasRestoredFilters || typeof window === "undefined") return;
    const payload = {
      date,
      searchTerm,
      sortKey,
      sortOrder,
      riskFilter,
    };
    window.localStorage.setItem(storageKey, JSON.stringify(payload));
  }, [date, searchTerm, sortKey, sortOrder, riskFilter, storageKey, hasRestoredFilters]);

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
      setIsFetching(true);
      setFetchError(null);
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
        setFetchError(getErrorMessage(err, "データの取得に失敗しました"));
      } finally {
        setIsFetching(false);
        setHasLoadedOnce(true);
      }
    },
    [fetcher]
  );

  const loadDates = useCallback(async () => {
    try {
      const result = await getAvailableDates();
      const dates = result.dates || [];
      setAvailableDates(dates);
      setDate((prev) => {
        if (prev && dates.includes(prev)) return prev;
        return dates[0] || "";
      });
      setDateError(null);
    } catch (err) {
      console.error("Failed to load dates", err);
      setDateError(getErrorMessage(err, "日付一覧の取得に失敗しました"));
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
  const processedData = useMemo(() => {
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

  const isInitialLoading = !hasLoadedOnce && isFetching;
  const isRefreshing = hasLoadedOnce && isFetching;
  const exportStatusText = useMemo(() => {
    if (!exporting) return null;
    if (exportStage === "building") return "CSVを生成中...";
    return "CSVデータを取得中...";
  }, [exporting, exportStage]);

  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;
  const controlsDisabled = isInitialLoading;

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
    setExportError(null);
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
    setExportError(null);

    const exportTotal = Math.min(total, CSV_MAX_ROWS);
    setExportStage("fetching");
    setExportProgress({ current: 0, total: exportTotal });

    try {
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

      const rows: string[] = [];
      let offset = 0;

      while (offset < exportTotal) {
        const limit = Math.min(EXPORT_PAGE_SIZE, exportTotal - offset);
        const batch = await fetcher(
          date || undefined,
          limit,
          offset,
          debouncedSearch || undefined
        );
        const items = batch.data || [];

        if (items.length === 0) break;

        for (const item of items) {
          const row = [
            item.risk_label || "-",
            item.ipaddress,
            `"${item.useragent.replace(/"/g, '""')}"`,
            item[metricKey] ?? 0,
            ...(metricKey === "total_conversions"
              ? [item.min_click_to_conv_seconds ?? "", item.max_click_to_conv_seconds ?? ""]
              : []),
            item.media_count,
            `"${(item.media_names || []).join(", ")}"`,
            item.program_count,
            `"${(item.program_names || []).join(", ")}"`,
            `"${readableReasonsFor(item).join(", ")}"`,
          ].join(",");
          rows.push(row);
        }

        offset += items.length;
        setExportProgress({ current: offset, total: exportTotal });
      }

      if (rows.length === 0) {
        setExportError("出力対象のデータがありませんでした。");
        return;
      }

      setExportStage("building");
      const csv = [headers.join(","), ...rows].join("\n");
      const bom = "\uFEFF";
      const blob = new Blob([bom + csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${csvPrefix}_${date}${debouncedSearch ? `_${debouncedSearch}` : ""}.csv`;
      a.click();
      URL.revokeObjectURL(url);

      notify({
        title: "CSV出力が完了しました",
        description: `${rows.length.toLocaleString()}件を出力しました。`,
        variant: "success",
        duration: 8000,
      });

      if (total > rows.length) {
        setExportError(`${rows.length.toLocaleString()}件を出力しました（全${total.toLocaleString()}件中）`);
      }
    } catch (err) {
      console.error("CSV export failed", err);
      const message = getErrorMessage(err, "CSV出力に失敗しました");
      setExportError(message);
      notify({
        title: "CSV出力に失敗しました",
        description: message,
        variant: "error",
        duration: null,
      });
    } finally {
      setExporting(false);
      setExportStage("idle");
      setExportProgress(null);
    }
  };

  // 統計サマリーの計算
  const stats = useMemo(
    () => ({
      high: data.filter((d) => d.risk_level === "high").length,
      medium: data.filter((d) => d.risk_level === "medium").length,
      low: data.filter((d) => d.risk_level === "low").length,
    }),
    [data]
  );

  const breadcrumbItems = useMemo(() => {
    const suspiciousHref =
      metricKey === "total_clicks" ? "/suspicious/clicks" : "/suspicious/conversions";
    return [
      { label: "ダッシュボード", href: "/" },
      { label: "不正検知", href: suspiciousHref },
      { label: title },
    ];
  }, [metricKey, title]);

  const riskCardBase = "bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm";

  const ariaSortValue = (key: SortKey) => {
    if (sortKey !== key) return "none";
    return sortOrder === "asc" ? "ascending" : "descending";
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
        <div className="space-y-2">
          <Breadcrumbs items={breadcrumbItems} />
          <div>
            <h2 className="text-2xl font-bold text-balance">{title}</h2>
            <p className="text-muted-foreground text-pretty">{description}</p>
          </div>
        </div>
        
        {/* 日付選択と更新コントロール */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start">
          <div className="flex flex-col gap-1">
            <DateQuickSelect
              value={date}
              onChange={handleDateChange}
              availableDates={availableDates}
              showQuickButtons={true}
            />
            {dateError && (
              <p className="text-xs text-destructive" role="alert">
                {dateError}
              </p>
            )}
          </div>
          
          <div className="flex flex-col items-start gap-1 sm:items-end">
            <div className="flex items-center gap-2">
              <LastUpdated
                lastUpdated={lastUpdated}
                onRefresh={handleRefresh}
                isRefreshing={isFetching}
                showAutoRefresh={true}
              />
              
              <Button
                size="sm"
                onClick={handleExportClick}
                disabled={total === 0 || exporting}
                className="h-8"
                aria-busy={exporting}
              >
                {exporting ? (
                  <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Download className="mr-1.5 h-3.5 w-3.5" />
                )}
                {exporting ? "出力中..." : "CSV"}
              </Button>
            </div>

            {exportStatusText && (
              <span className="text-xs text-muted-foreground">{exportStatusText}</span>
            )}
            {exportProgress && (
              <span className="text-xs tabular-nums text-muted-foreground" aria-live="polite">
                CSV出力: {exportProgress.current.toLocaleString()} / {exportProgress.total.toLocaleString()}
              </span>
            )}
            {exportError && (
              <span className="text-xs text-destructive" role="alert">
                {exportError}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* リスク別サマリーカード */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-balance">総検知数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tabular-nums">{total.toLocaleString()}</div>
          </CardContent>
        </Card>
        <button
          type="button"
          className={cn(
            riskCardBase,
            "text-left",
            riskFilter === "high" ? "ring-2 ring-red-500" : "hover:shadow-md"
          )}
          onClick={() => setRiskFilter(riskFilter === "high" ? "all" : "high")}
          aria-pressed={riskFilter === "high"}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-balance flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-500" />
              高リスク
            </CardTitle>
            <CardDescription className="text-xs text-pretty">クリックでフィルタ切替</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600 tabular-nums">{stats.high}</div>
          </CardContent>
        </button>
        <button
          type="button"
          className={cn(
            riskCardBase,
            "text-left",
            riskFilter === "medium" ? "ring-2 ring-yellow-500" : "hover:shadow-md"
          )}
          onClick={() => setRiskFilter(riskFilter === "medium" ? "all" : "medium")}
          aria-pressed={riskFilter === "medium"}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-balance flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              中リスク
            </CardTitle>
            <CardDescription className="text-xs text-pretty">クリックでフィルタ切替</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600 tabular-nums">{stats.medium}</div>
          </CardContent>
        </button>
        <button
          type="button"
          className={cn(
            riskCardBase,
            "text-left",
            riskFilter === "low" ? "ring-2 ring-blue-500" : "hover:shadow-md"
          )}
          onClick={() => setRiskFilter(riskFilter === "low" ? "all" : "low")}
          aria-pressed={riskFilter === "low"}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-balance flex items-center gap-2">
              <Info className="h-4 w-4 text-blue-500" />
              低リスク
            </CardTitle>
            <CardDescription className="text-xs text-pretty">クリックでフィルタ切替</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600 tabular-nums">{stats.low}</div>
          </CardContent>
        </button>
      </div>

      {/* CSV出力警告ダイアログ */}
      <Dialog open={csvWarningOpen} onOpenChange={setCsvWarningOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-balance">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              CSV出力の制限
            </DialogTitle>
            <DialogDescription className="pt-2 text-pretty tabular-nums">
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
              <CardTitle className="flex items-center gap-2 text-balance">
                検知リスト ({date || "データなし"})
                {isRefreshing && (
                  <Badge variant="outline" className="text-xs">
                    更新中
                  </Badge>
                )}
              </CardTitle>
              <CardDescription className="text-pretty">
                {riskFilter !== "all" && (
                  <Badge variant="secondary" className="mr-2">
                    {RISK_CONFIG[riskFilter as keyof typeof RISK_CONFIG]?.label}でフィルタ中
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setRiskFilter("all")}
                      className="ml-1"
                      aria-label="リスクフィルタを解除"
                      type="button"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                )}
                <span className="tabular-nums" aria-live="polite">
                  {processedData.length}件表示 / 全{total}件
                </span>
                <span className="ml-2 text-xs text-muted-foreground">(表示中のデータにフィルタを適用)</span>
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative w-full max-w-sm">
                <Label htmlFor={searchId} className="sr-only">
                  検索
                </Label>
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" aria-hidden="true" />
                <Input
                  id={searchId}
                  placeholder="IP・UA・媒体名・案件名で検索..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 w-[300px]"
                />
                {searchTerm && searchTerm !== debouncedSearch && (
                  <Loader2 className="absolute right-2.5 top-2.5 h-4 w-4 animate-spin text-muted-foreground" aria-hidden="true" />
                )}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {fetchError && (
            <div
              className="mb-3 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
              role="alert"
            >
              <div className="font-medium">データ取得に失敗しました</div>
              <div className="text-xs text-destructive/80 text-pretty">{fetchError}</div>
              <div className="mt-2">
                <Button variant="outline" size="sm" onClick={handleRefresh}>
                  再試行
                </Button>
              </div>
            </div>
          )}
          {isInitialLoading ? (
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
                      <TableHead className="w-[100px]" aria-sort={ariaSortValue("risk")}>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-8 px-2"
                          onClick={() => toggleSort("risk")}
                          aria-label="リスクで並べ替え"
                        >
                          リスク
                          {sortIcon("risk")}
                        </Button>
                      </TableHead>
                      <TableHead className="w-[130px]">{ipLabel}</TableHead>
                      <TableHead className="text-right" aria-sort={ariaSortValue("count")}>
                        <div className="flex items-center justify-end">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-8 px-2"
                            onClick={() => toggleSort("count")}
                            aria-label={`${countLabel}で並べ替え`}
                          >
                            {countLabel}
                            {sortIcon("count")}
                          </Button>
                        </div>
                      </TableHead>
                      {metricKey === "total_conversions" && (
                        <TableHead className="text-center">経過時間</TableHead>
                      )}
                      <TableHead className="text-center" aria-sort={ariaSortValue("media")}>
                        <div className="flex items-center justify-center">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-8 px-2"
                            onClick={() => toggleSort("media")}
                            aria-label="媒体数で並べ替え"
                          >
                            媒体
                            {sortIcon("media")}
                          </Button>
                        </div>
                      </TableHead>
                      <TableHead className="text-center" aria-sort={ariaSortValue("program")}>
                        <div className="flex items-center justify-center">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-8 px-2"
                            onClick={() => toggleSort("program")}
                            aria-label="案件数で並べ替え"
                          >
                            案件
                            {sortIcon("program")}
                          </Button>
                        </div>
                      </TableHead>
                      <TableHead>判定理由</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {processedData.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={metricKey === "total_conversions" ? 8 : 7} className="h-24 text-center">
                          データが見つかりません
                        </TableCell>
                      </TableRow>
                    ) : (
                      processedData.map((item, i) => {
                        const rowId = `${item.ipaddress}-${i}`;
                        const isExpanded = expandedRows.has(rowId);
                        const riskConfig = RISK_CONFIG[item.risk_level || "low"];
                        const RiskIcon = riskConfig.icon;
                        const readableReasons = readableReasonsFor(item);

                        return (
                          <Fragment key={rowId}>
                            <TableRow className={cn(isExpanded && riskConfig.bgColor)}>
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
                                        className={cn(riskConfig.color, "flex items-center gap-1")}
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
                              <TableCell className="text-right font-bold text-lg tabular-nums">
                                {item[metricKey] ?? 0}
                              </TableCell>
                              {metricKey === "total_conversions" && (
                                <TableCell className="text-center text-xs font-mono tabular-nums">
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
                                  <span className="font-bold tabular-nums">{item.media_count}</span>
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
                                  <span className="font-bold tabular-nums">{item.program_count}</span>
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
                                  {readableReasons.slice(0, 2).map((reason, idx) => (
                                    <Badge key={idx} variant="secondary" className="text-xs">
                                      {reason}
                                    </Badge>
                                  ))}
                                  {readableReasons.length > 2 && (
                                    <Badge variant="outline" className="text-xs">
                                      +{readableReasons.length - 2}
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
                                        {readableReasons.map((r, idx) => (
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
                                                  <TableCell className="text-xs text-right py-2 font-medium tabular-nums">
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
                  <div className="text-sm text-muted-foreground tabular-nums">
                    {(page - 1) * PAGE_SIZE + 1} - {Math.min(page * PAGE_SIZE, total)} / {total}件
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(1)}
                      disabled={page === 1 || controlsDisabled}
                      aria-label="最初のページへ"
                    >
                      <ChevronsLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(page - 1)}
                      disabled={page === 1 || controlsDisabled}
                      aria-label="前のページへ"
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
                      disabled={page === totalPages || controlsDisabled}
                      aria-label="次のページへ"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(totalPages)}
                      disabled={page === totalPages || controlsDisabled}
                      aria-label="最後のページへ"
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
