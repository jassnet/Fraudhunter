"use client";

import { useJobStatus } from "@/hooks/use-job-status";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle, XCircle, Clock } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function JobStatusIndicator() {
  const { jobState, error } = useJobStatus();

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
          <Badge variant="default" asChild className="bg-blue-500 hover:bg-blue-600">
            <button type="button" className="inline-flex items-center gap-1">
              <Loader2 className="mr-1 h-3 w-3 motion-safe:animate-spin" />
              実行中
            </button>
          </Badge>
        );
      case "completed":
        return (
          <Badge variant="outline" asChild className="text-green-600 border-green-300">
            <button type="button" className="inline-flex items-center gap-1">
              <CheckCircle className="mr-1 h-3 w-3" />
              完了
            </button>
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="outline" asChild className="text-red-600 border-red-300">
            <button type="button" className="inline-flex items-center gap-1">
              <XCircle className="mr-1 h-3 w-3" />
              失敗
            </button>
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" asChild className="text-muted-foreground">
            <button type="button" className="inline-flex items-center gap-1">
              <Clock className="mr-1 h-3 w-3" />
              待機中
            </button>
          </Badge>
        );
    }
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          {getStatusContent()}
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          <div className="space-y-1 text-xs text-pretty">
            <div className="font-medium">
              {jobState.status === "running"
                ? "ジョブが実行中です"
                : jobState.status === "completed"
                ? "直近のジョブが完了しました"
                : jobState.status === "failed"
                ? "直近のジョブが失敗しました"
                : "まだジョブはありません"}
            </div>
            {jobState.job_id && (
              <div className="text-muted-foreground">ID: {jobState.job_id}</div>
            )}
            {jobState.message && (
              <div className="text-muted-foreground">{jobState.message}</div>
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
