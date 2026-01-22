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
          <Badge variant="default" className="bg-blue-500 hover:bg-blue-600 cursor-pointer">
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            Running
          </Badge>
        );
      case "completed":
        return (
          <Badge variant="outline" className="text-green-600 border-green-300 cursor-pointer">
            <CheckCircle className="mr-1 h-3 w-3" />
            Completed
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="outline" className="text-red-600 border-red-300 cursor-pointer">
            <XCircle className="mr-1 h-3 w-3" />
            Failed
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-muted-foreground cursor-pointer">
            <Clock className="mr-1 h-3 w-3" />
            Idle
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
              {jobState.status === "running"
                ? "Job is running"
                : jobState.status === "completed"
                ? "Last job completed"
                : jobState.status === "failed"
                ? "Last job failed"
                : "No job yet"}
            </div>
            {jobState.job_id && (
              <div className="text-muted-foreground">ID: {jobState.job_id}</div>
            )}
            {jobState.message && (
              <div className="text-muted-foreground">{jobState.message}</div>
            )}
            {jobState.started_at && (
              <div className="text-muted-foreground">
                Started: {formatTime(jobState.started_at)}
              </div>
            )}
            {jobState.completed_at && (
              <div className="text-muted-foreground">
                Completed: {formatTime(jobState.completed_at)}
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
