"use client";

import { useEffect, useMemo, useState } from "react";
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
import { ingestClicks, ingestConversions, syncMasters, getMastersStatus, MasterStatus } from "@/lib/api";
import { Loader2, CheckCircle, XCircle, Clock, Database, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useJobRunner } from "@/lib/use-job-runner";

interface RefreshDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
  initialDate?: string;
}

export function RefreshDialog({ open, onOpenChange, onSuccess, initialDate }: RefreshDialogProps) {
  const [date, setDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    return d.toISOString().split("T")[0];
  });
  const [masterStatus, setMasterStatus] = useState<MasterStatus | null>(null);
  const [masterSyncing, setMasterSyncing] = useState(false);

  const { status, message, jobId, jobResult, loading, runJob, reset } = useJobRunner(onSuccess);

  const buttonDisabled = useMemo(() => loading || status === "running", [loading, status]);

  const MASTER_SYNC_THRESHOLD_HOURS = 48;

  const lastSyncedDate = useMemo(() => {
    if (!masterStatus?.last_synced_at) return null;
    const parsed = new Date(masterStatus.last_synced_at);
    return isNaN(parsed.getTime()) ? null : parsed;
  }, [masterStatus]);

  const needsMasterSync = useMemo(() => {
    if (!lastSyncedDate) return true;
    const diffHours = (Date.now() - lastSyncedDate.getTime()) / (1000 * 60 * 60);
    return diffHours >= MASTER_SYNC_THRESHOLD_HOURS;
  }, [lastSyncedDate]);

  const loadMasterStatus = async () => {
    try {
      const result = await getMastersStatus();
      setMasterStatus(result);
    } catch (err) {
      console.error("Failed to load master status", err);
    }
  };

  useEffect(() => {
    if (open) {
      loadMasterStatus();
    }
  }, [open]);

  useEffect(() => {
    if (!open || !initialDate) return;
    setDate(initialDate);
  }, [open, initialDate]);

  const ensureMasterSynced = async () => {
    if (!needsMasterSync || masterSyncing) return;
    setMasterSyncing(true);
    try {
      await syncMasters();
      await loadMasterStatus();
    } catch (err) {
      console.error("Master sync failed", err);
    } finally {
      setMasterSyncing(false);
    }
  };

  const handleIngestClicks = () =>
    runJob(`ingest_clicks_${date}`, "クリックログを取り込み中...", async () => {
      await ensureMasterSynced();
      return ingestClicks(date);
    });

  const handleIngestConversions = () =>
    runJob(`ingest_conversions_${date}`, "成果ログを取り込み中...", async () => {
      await ensureMasterSynced();
      return ingestConversions(date);
    });

  const handleSyncMasters = () =>
    runJob("sync_masters", "マスタデータを同期中...", () => syncMasters());

  const handleClose = (openState: boolean) => {
    if (!openState) {
      reset();
    }
    onOpenChange(openState);
  };

  const handleRetry = () => {
    reset();
  };

  const handleDone = () => {
    reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>データ取り込み</DialogTitle>
          <DialogDescription>ACS APIからログデータを取得してDBに保存します</DialogDescription>
        </DialogHeader>

        {status === "idle" && (
          <Tabs defaultValue="date" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="date">日付指定</TabsTrigger>
              <TabsTrigger value="master">マスタ同期</TabsTrigger>
            </TabsList>

            <TabsContent value="date" className="space-y-4">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>
                  マスタ最終同期:{" "}
                  {lastSyncedDate
                    ? lastSyncedDate.toLocaleString("ja-JP", { hour12: false })
                    : "未同期"}
                </span>
                {needsMasterSync && (
                  <Badge variant="secondary" className="ml-2">
                    48時間超で自動同期
                  </Badge>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="date">対象日付</Label>
                <Input id="date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
              </div>
              <div className="flex space-x-2">
                <Button onClick={handleIngestClicks} disabled={buttonDisabled} className="flex-1">
                  {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  クリックログ取込
                </Button>
                <Button
                  onClick={handleIngestConversions}
                  disabled={buttonDisabled}
                  variant="secondary"
                  className="flex-1"
                >
                  {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  成果ログ取込
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="master" className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  ACSから媒体・案件・アフィリエイター情報を取得し、名前表示に使用するマスタデータを更新します。
                </p>
              </div>
              <DialogFooter>
                <Button onClick={handleSyncMasters} disabled={buttonDisabled}>
                  <Database className="mr-2 h-4 w-4" />
                  マスタ同期開始
                </Button>
              </DialogFooter>
            </TabsContent>
          </Tabs>
        )}

        {status === "running" && (
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <p className="text-muted-foreground text-center">{message}</p>
            {jobId && (
              <Badge variant="outline" className="font-mono text-xs">
                <Clock className="mr-1 h-3 w-3" />
                {jobId}
              </Badge>
            )}
            <p className="text-xs text-muted-foreground">バックグラウンドで処理中です...</p>
            <p className="text-xs text-muted-foreground">このダイアログを閉じても処理は継続されます</p>
          </div>
        )}

        {status === "success" && (
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <CheckCircle className="h-12 w-12 text-green-500" />
            <p className="text-center font-medium">処理が完了しました</p>

            {jobResult && (
              <div className="w-full space-y-2 text-sm border rounded-lg p-4 bg-muted/50">
                {jobResult.clicks && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">クリック</span>
                    <span>
                      新規: {jobResult.clicks.new} / スキップ: {jobResult.clicks.skipped}
                    </span>
                  </div>
                )}
                {jobResult.conversions && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">成果</span>
                    <span>
                      新規: {jobResult.conversions.new} / スキップ: {jobResult.conversions.skipped}
                    </span>
                  </div>
                )}
                {jobResult.count !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">取込件数</span>
                    <span>{jobResult.count}件</span>
                  </div>
                )}
                {jobResult.total !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">総件数</span>
                    <span>{jobResult.total}件</span>
                  </div>
                )}
              </div>
            )}

            <DialogFooter className="w-full">
              <Button onClick={handleDone} className="w-full">
                閉じる
              </Button>
            </DialogFooter>
          </div>
        )}

        {status === "error" && (
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <XCircle className="h-12 w-12 text-red-500" />
            <p className="text-center font-medium text-red-500">エラーが発生しました</p>
            <div className="w-full border border-red-200 rounded-lg p-4 bg-red-50 dark:bg-red-950/20">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-600 dark:text-red-400 break-all">{message}</p>
              </div>
            </div>
            <div className="flex gap-2 w-full">
              <Button onClick={handleRetry} variant="outline" className="flex-1">
                再試行
              </Button>
              <Button onClick={handleDone} variant="ghost" className="flex-1">
                閉じる
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
