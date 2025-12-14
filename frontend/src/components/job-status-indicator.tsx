"use client";

import { useCallback, useEffect, useState } from "react";
import { getJobStatus } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle, XCircle, Clock } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface JobState {
  status: string;
  job_id?: string | null;
  message?: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export function JobStatusIndicator() {
  const [jobState, setJobState] = useState<JobState | null>(null);
  const [error, setError] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const status = await getJobStatus();
      setJobState(status);
      setError(false);
    } catch (e) {
      console.error("Failed to fetch job status", e);
      setError(true);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    // ポーリング間隔: running時は2秒、それ以外は10秒
    const interval = setInterval(() => {
      fetchStatus();
    }, jobState?.status === "running" ? 2000 : 10000);

    return () => clearInterval(interval);
  }, [fetchStatus, jobState?.status]);

  if (error || !jobState) {
    return null;
  }

  const formatTime = (isoString: string | null | undefined) => {
    if (!isoString) return "";
    try {
      return new Date(isoString).toLocaleString("ja-JP", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  const getStatusContent = () => {
    switch (jobState.status) {
      case "running":
        return (
          <Badge variant="default" className="bg-blue-500 hover:bg-blue-600 cursor-pointer">
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            実行中
          </Badge>
        );
      case "completed":
        return (
          <Badge variant="outline" className="text-green-600 border-green-300 cursor-pointer">
            <CheckCircle className="mr-1 h-3 w-3" />
            完了
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="outline" className="text-red-600 border-red-300 cursor-pointer">
            <XCircle className="mr-1 h-3 w-3" />
            失敗
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-muted-foreground cursor-pointer">
            <Clock className="mr-1 h-3 w-3" />
            待機中
          </Badge>
        );
    }
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="inline-flex">{getStatusContent()}</div>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          <div className="space-y-1 text-xs">
            <div className="font-medium">
              {jobState.status === "running" ? "ジョブ実行中" :
               jobState.status === "completed" ? "最後のジョブが完了" :
               jobState.status === "failed" ? "最後のジョブが失敗" :
               "ジョブなし"}
            </div>
            {jobState.job_id && (
              <div className="text-muted-foreground">
                ID: {jobState.job_id}
              </div>
            )}
            {jobState.message && (
              <div className="text-muted-foreground">
                {jobState.message}
              </div>
            )}
            {jobState.started_at && (
              <div className="text-muted-foreground">
                開始: {formatTime(jobState.started_at)}
              </div>
            )}
            {jobState.completed_at && (
              <div className="text-muted-foreground">
                完了: {formatTime(jobState.completed_at)}
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

