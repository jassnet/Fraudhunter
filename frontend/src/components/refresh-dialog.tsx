"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ingestClicks, ingestConversions, refreshData, getJobStatus } from "@/lib/api";
import { Loader2, CheckCircle, XCircle, Clock } from "lucide-react";

interface RefreshDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function RefreshDialog({ open, onOpenChange, onSuccess }: RefreshDialogProps) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "running" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const [date, setDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    return d.toISOString().split('T')[0];
  });
  const [hours, setHours] = useState(24);

  // ジョブステータスをポーリング
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (status === "running") {
      interval = setInterval(async () => {
        try {
          const jobStatus = await getJobStatus();
          if (jobStatus.status === "completed") {
            setStatus("success");
            setMessage(jobStatus.message);
            onSuccess?.();
          } else if (jobStatus.status === "failed") {
            setStatus("error");
            setMessage(jobStatus.message);
          }
        } catch (e) {
          console.error("Failed to get job status", e);
        }
      }, 2000);
    }
    
    return () => clearInterval(interval);
  }, [status, onSuccess]);

  const handleIngestClicks = async () => {
    setLoading(true);
    setStatus("running");
    setMessage("クリックログを取り込み中...");
    try {
      await ingestClicks(date);
    } catch (e: any) {
      setStatus("error");
      setMessage(e.message || "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  const handleIngestConversions = async () => {
    setLoading(true);
    setStatus("running");
    setMessage("成果ログを取り込み中...");
    try {
      await ingestConversions(date);
    } catch (e: any) {
      setStatus("error");
      setMessage(e.message || "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    setStatus("running");
    setMessage(`過去${hours}時間のデータを取り込み中...`);
    try {
      await refreshData(hours, true, true);
    } catch (e: any) {
      setStatus("error");
      setMessage(e.message || "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (status !== "running") {
      setStatus("idle");
      setMessage("");
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>データ取り込み</DialogTitle>
          <DialogDescription>
            ACS APIからログデータを取得してDBに保存します
          </DialogDescription>
        </DialogHeader>

        {status === "idle" && (
          <Tabs defaultValue="refresh" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="refresh">リフレッシュ</TabsTrigger>
              <TabsTrigger value="date">日付指定</TabsTrigger>
            </TabsList>
            
            <TabsContent value="refresh" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="hours">取得時間範囲（時間）</Label>
                <Input
                  id="hours"
                  type="number"
                  value={hours}
                  onChange={(e) => setHours(parseInt(e.target.value) || 24)}
                  min={1}
                  max={168}
                />
                <p className="text-sm text-muted-foreground">
                  現在時刻から指定時間前までのデータを取得します。重複データは自動でスキップされます。
                </p>
              </div>
              <DialogFooter>
                <Button onClick={handleRefresh} disabled={loading}>
                  {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  取り込み開始
                </Button>
              </DialogFooter>
            </TabsContent>
            
            <TabsContent value="date" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="date">対象日付</Label>
                <Input
                  id="date"
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </div>
              <div className="flex space-x-2">
                <Button onClick={handleIngestClicks} disabled={loading} className="flex-1">
                  {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  クリックログ取込
                </Button>
                <Button onClick={handleIngestConversions} disabled={loading} variant="secondary" className="flex-1">
                  {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  成果ログ取込
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        )}

        {status === "running" && (
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <p className="text-muted-foreground">{message}</p>
            <p className="text-xs text-muted-foreground">
              バックグラウンドで処理中です。しばらくお待ちください...
            </p>
          </div>
        )}

        {status === "success" && (
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <CheckCircle className="h-12 w-12 text-green-500" />
            <p className="text-center">{message}</p>
            <Button onClick={handleClose}>閉じる</Button>
          </div>
        )}

        {status === "error" && (
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <XCircle className="h-12 w-12 text-red-500" />
            <p className="text-center text-red-500">{message}</p>
            <Button onClick={() => setStatus("idle")} variant="outline">
              再試行
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

