"use client";

import { useEffect, useState } from "react";
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
import { Search, Download, RefreshCw } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchSuspiciousConversions } from "@/lib/api";

type SuspiciousConversion = {
  date: string;
  ipaddress: string;
  useragent: string;
  total_conversions: number;
  media_count: number;
  program_count: number;
  first_time: string;
  last_time: string;
};

export default function SuspiciousConversionsPage() {
  const [data, setData] = useState<SuspiciousConversion[]>([]);
  const [loading, setLoading] = useState(true);
  const [date, setDate] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState("");
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const json = await fetchSuspiciousConversions(date || undefined);
      if (json.data) {
          setData(json.data);
          if (!date && json.date) setDate(json.date);
      }
    } catch (err) {
      console.error(err);
      setError("データの取得に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredData = data.filter(item => 
    item.ipaddress.includes(searchTerm) || 
    item.useragent.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const exportCSV = () => {
    const headers = ["IPアドレス", "UserAgent", "成果数", "媒体数", "案件数", "開始時刻", "終了時刻"];
    const rows = filteredData.map(item => [
      item.ipaddress,
      `"${item.useragent.replace(/"/g, '""')}"`,
      item.total_conversions,
      item.media_count,
      item.program_count,
      item.first_time,
      item.last_time
    ]);
    
    const csv = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `suspicious_conversions_${date}.csv`;
    a.click();
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">不正成果検知</h2>
          <p className="text-muted-foreground">
            実ユーザーIPベースでの不正成果パターン検出（ポストバック経由含む）
          </p>
        </div>
        <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
                <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
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
          <CardTitle>検知リスト ({date || "データなし"})</CardTitle>
          <CardDescription>
            成果数5回以上、または複数媒体・複数案件での成果発生
          </CardDescription>
          <div className="flex items-center py-4">
            <div className="relative w-full max-w-sm">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                placeholder="IPアドレスまたはUAで検索..."
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
                <div className="rounded-md border">
                    <Table>
                    <TableHeader>
                        <TableRow>
                        <TableHead className="w-[140px]">実IPアドレス</TableHead>
                        <TableHead className="max-w-[300px]">User Agent</TableHead>
                        <TableHead className="text-right">成果数</TableHead>
                        <TableHead className="text-center">媒体数</TableHead>
                        <TableHead className="text-center">案件数</TableHead>
                        <TableHead>期間</TableHead>
                        <TableHead className="text-right">判定</TableHead>
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
                                <TableRow key={i}>
                                    <TableCell className="font-medium font-mono text-xs">{item.ipaddress}</TableCell>
                                    <TableCell className="max-w-[300px] truncate text-xs" title={item.useragent}>
                                        {item.useragent}
                                    </TableCell>
                                    <TableCell className="text-right font-bold">{item.total_conversions}</TableCell>
                                    <TableCell className="text-center">{item.media_count}</TableCell>
                                    <TableCell className="text-center">{item.program_count}</TableCell>
                                    <TableCell className="text-xs text-muted-foreground">
                                        {item.first_time?.split(' ')[1] || '-'} - {item.last_time?.split(' ')[1] || '-'}
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Badge variant="destructive">Critical</Badge>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                    </Table>
                </div>
            )}
        </CardContent>
      </Card>
    </div>
  );
}
