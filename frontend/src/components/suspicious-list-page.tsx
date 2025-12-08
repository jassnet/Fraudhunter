"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Search,
  Download,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Calendar,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  SuspiciousItem,
  SuspiciousResponse,
  getAvailableDates,
} from "@/lib/api";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

type MetricKey = "total_clicks" | "total_conversions";
type SuspiciousFetcher = (
  date?: string,
  limit?: number,
  offset?: number
) => Promise<SuspiciousResponse>;

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
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [selectedItem, setSelectedItem] = useState<SuspiciousItem | null>(null);

  const fetchData = useCallback(
    async (targetDate: string | undefined, pageNum: number) => {
      setLoading(true);
      setError(null);
      try {
        const offset = (pageNum - 1) * PAGE_SIZE;
        const json = await fetcher(targetDate || undefined, PAGE_SIZE, offset);
        if (json.data) {
          setData(json.data);
          setTotal(json.total);
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
      setAvailableDates(result.dates || []);
    } catch (err) {
      console.error("Failed to load dates", err);
    }
  }, []);

  useEffect(() => {
    loadDates();
  }, [loadDates]);

  useEffect(() => {
    fetchData(date || undefined, page);
  }, [date, page, fetchData]);

  const filteredData = useMemo(
    () =>
      data.filter((item) =>
        item.ipaddress.includes(searchTerm) ||
        item.useragent.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.media_names?.some((n) => n.toLowerCase().includes(searchTerm.toLowerCase())) ||
        item.program_names?.some((n) => n.toLowerCase().includes(searchTerm.toLowerCase()))
      ),
    [data, searchTerm]
  );

  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;

  const handlePageChange = (newPage: number) => {
    const nextPage = Math.min(Math.max(newPage, 1), totalPages);
    setPage(nextPage);
  };

  const exportCSV = () => {
    if (filteredData.length === 0) return;

    const headers = [
      ipLabel,
      "User Agent",
      countLabel,
      ...(metricKey === "total_conversions" ? ["最短経過時間(秒)", "最長経過時間(秒)"] : []),
      "媒体",
      "案件",
      "判定理由",
    ];

    const rows = filteredData.map((item) => [
      item.ipaddress,
      `"${item.useragent.replace(/"/g, '""')}"`,
      item[metricKey] ?? 0,
      ...(metricKey === "total_conversions" ? [
        item.min_click_to_conv_seconds ?? "",
        item.max_click_to_conv_seconds ?? ""
      ] : []),
      `"${(item.media_names || []).join(", ")}"`,
      `"${(item.program_names || []).join(", ")}"`,
      `"${(item.reasons_formatted || item.reasons || []).join(", ")}"`,
    ]);

    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const bom = "\uFEFF";
    const blob = new Blob([bom + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${csvPrefix}_${date}.csv`;
    a.click();
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div className="flex items-center space-x-2 ml-auto">
          <Select
            value={date}
            onValueChange={(value) => {
              setPage(1);
              setDate(value);
            }}
          >
            <SelectTrigger className="w-[180px]">
              <Calendar className="mr-2 h-4 w-4" />
              <SelectValue placeholder="日付を選択" />
            </SelectTrigger>
            <SelectContent>
              {availableDates.map((d) => (
                <SelectItem key={d} value={d}>
                  {d}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchData(date, page)}
            disabled={loading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            更新
          </Button>
          <Button size="sm" onClick={exportCSV} disabled={filteredData.length === 0}>
            <Download className="mr-2 h-4 w-4" />
            CSV出力
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>検知リスト ({date || "データなし"}) - 全{total}件</CardTitle>
          <div className="flex items-center py-4">
            <div className="relative w-full max-w-sm">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="IP・UA・媒体名・案件名で検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="text-center py-8 text-red-500">{error}</div>
          ) : loading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[140px]">{ipLabel}</TableHead>
                      <TableHead className="max-w-[200px]">User Agent</TableHead>
                      <TableHead className="text-right">{countLabel}</TableHead>
                      {metricKey === "total_conversions" && (
                        <TableHead className="text-center">経過時間</TableHead>
                      )}
                      <TableHead className="text-center">媒体</TableHead>
                      <TableHead className="text-center">案件</TableHead>
                      <TableHead>判定理由</TableHead>
                      <TableHead className="text-right">詳細</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredData.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="h-24 text-center">
                          データが見つかりません
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredData.map((item, i) => (
                        <TableRow key={`${item.ipaddress}-${i}`}>
                          <TableCell className="font-medium font-mono text-xs">
                            {item.ipaddress}
                          </TableCell>
                          <TableCell className="max-w-[200px] truncate text-xs" title={item.useragent}>
                            {item.useragent}
                          </TableCell>
                          <TableCell className="text-right font-bold">
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
                            <div className="text-xs">
                              <span className="font-medium">{item.media_count}</span>
                              {item.media_names && item.media_names.length > 0 && (
                                <div
                                  className="text-muted-foreground truncate max-w-[100px]"
                                  title={item.media_names.join(", ")}
                                >
                                  {item.media_names[0]}
                                  {item.media_names.length > 1 && ` +${item.media_names.length - 1}`}
                                </div>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="text-xs">
                              <span className="font-medium">{item.program_count}</span>
                              {item.program_names && item.program_names.length > 0 && (
                                <div
                                  className="text-muted-foreground truncate max-w-[100px]"
                                  title={item.program_names.join(", ")}
                                >
                                  {item.program_names[0]}
                                  {item.program_names.length > 1 && ` +${item.program_names.length - 1}`}
                                </div>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-1">
                              {(item.reasons_formatted || item.reasons || []).map((reason, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs">
                                  {reason}
                                </Badge>
                              ))}
                            </div>
                          </TableCell>
                          <TableCell className="text-right">
                            <Dialog>
                              <DialogTrigger asChild>
                                <Button variant="ghost" size="sm" onClick={() => setSelectedItem(item)}>
                                  詳細
                                </Button>
                              </DialogTrigger>
                              <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                                <DialogHeader>
                                  <DialogTitle>詳細情報</DialogTitle>
                                </DialogHeader>
                                {selectedItem && (
                                  <div className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                      <div>
                                        <label className="font-medium text-muted-foreground">{ipLabel}</label>
                                        <p className="font-mono">{selectedItem.ipaddress}</p>
                                      </div>
                                      <div>
                                        <label className="font-medium text-muted-foreground">{countLabel}</label>
                                        <p className="font-bold text-lg">{selectedItem[metricKey] ?? 0}</p>
                                      </div>
                                    </div>
                                    {(selectedItem.min_click_to_conv_seconds !== undefined || selectedItem.max_click_to_conv_seconds !== undefined) && (
                                      <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div>
                                          <label className="font-medium text-muted-foreground">最短経過時間</label>
                                          <p className="font-mono">
                                            {selectedItem.min_click_to_conv_seconds !== null && selectedItem.min_click_to_conv_seconds !== undefined
                                              ? `${Math.round(selectedItem.min_click_to_conv_seconds)}秒`
                                              : "-"}
                                          </p>
                                        </div>
                                        <div>
                                          <label className="font-medium text-muted-foreground">最長経過時間</label>
                                          <p className="font-mono">
                                            {selectedItem.max_click_to_conv_seconds !== null && selectedItem.max_click_to_conv_seconds !== undefined
                                              ? `${Math.round(selectedItem.max_click_to_conv_seconds)}秒`
                                              : "-"}
                                          </p>
                                        </div>
                                      </div>
                                    )}
                                    <div>
                                      <label className="font-medium text-muted-foreground">User Agent</label>
                                      <p className="text-xs break-all">{selectedItem.useragent}</p>
                                    </div>
                                    <div>
                                      <label className="font-medium text-muted-foreground">判定理由</label>
                                      <div className="flex flex-wrap gap-1 mt-1">
                                        {(selectedItem.reasons_formatted || selectedItem.reasons || []).map((r, idx) => (
                                          <Badge key={idx} variant="destructive">
                                            {r}
                                          </Badge>
                                        ))}
                                      </div>
                                    </div>
                                    {selectedItem.details && selectedItem.details.length > 0 && (
                                      <div>
                                        <label className="font-medium text-muted-foreground">関連媒体・案件</label>
                                        <Table className="mt-2">
                                          <TableHeader>
                                            <TableRow>
                                              <TableHead>媒体名</TableHead>
                                              <TableHead>案件名</TableHead>
                                              <TableHead className="text-right">{countLabel}</TableHead>
                                            </TableRow>
                                          </TableHeader>
                                          <TableBody>
                                            {selectedItem.details.map((d, idx) => (
                                              <TableRow key={`${d.media_id}-${d.program_id}-${idx}`}>
                                                <TableCell className="text-xs">{d.media_name}</TableCell>
                                                <TableCell className="text-xs">{d.program_name}</TableCell>
                                                <TableCell className="text-right">
                                                  {metricKey === "total_clicks" ? d.click_count : d.conversion_count}
                                                </TableCell>
                                              </TableRow>
                                            ))}
                                          </TableBody>
                                        </Table>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </DialogContent>
                            </Dialog>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>

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
