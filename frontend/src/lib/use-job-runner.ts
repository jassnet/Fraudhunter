"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getJobStatus } from "./api";

type Status = "idle" | "running" | "success" | "error";

interface JobResult {
  success?: boolean;
  clicks?: { new: number; skipped: number };
  conversions?: { new: number; skipped: number; valid_entry?: number };
  count?: number;
  total?: number;
  enriched?: number;
  error?: string;
  [key: string]: unknown;
}

interface JobState {
  status: string;
  job_id?: string | null;
  message?: string;
  started_at?: string | null;
  completed_at?: string | null;
  result?: JobResult | null;
}

export function useJobRunner(onSuccess?: () => void) {
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobResult, setJobResult] = useState<JobResult | null>(null);
  const [loading, setLoading] = useState(false);
  const pollTimer = useRef<NodeJS.Timeout | null>(null);

  const stopPolling = () => {
    if (pollTimer.current) {
      clearInterval(pollTimer.current);
      pollTimer.current = null;
    }
  };

  const pollJobStatus = useCallback(async () => {
    try {
      const jobStatus: JobState = await getJobStatus();
      if (jobStatus.status === "running") {
        setStatus("running");
        setMessage(jobStatus.message || "ジョブを実行中です");
        setJobId(jobStatus.job_id || null);
        return true;
      }

      if (jobStatus.status === "completed") {
        setStatus("success");
        setMessage(jobStatus.message || "ジョブが完了しました");
        setJobId(jobStatus.job_id || null);
        setJobResult(jobStatus.result || null);
        onSuccess?.();
        return false;
      }

      if (jobStatus.status === "failed") {
        setStatus("error");
        setMessage(jobStatus.message || "ジョブが失敗しました");
        setJobId(jobStatus.job_id || null);
        setJobResult(jobStatus.result || null);
        return false;
      }

      setStatus("idle");
      setMessage(jobStatus.message || "");
      setJobId(jobStatus.job_id || null);
      setJobResult(jobStatus.result || null);
      return false;
    } catch (e) {
      console.error("Failed to poll job status", e);
      setStatus("error");
      setMessage("ジョブ状態の取得に失敗しました");
      return false;
    }
  }, [onSuccess]);

  useEffect(() => {
    if (status === "running" && !pollTimer.current) {
      pollTimer.current = setInterval(async () => {
        const shouldContinue = await pollJobStatus();
        if (!shouldContinue) {
          stopPolling();
        }
      }, 2000);
    }
    return stopPolling;
  }, [status, pollJobStatus]);

  const runJob = useCallback(
    async (jobId: string, runningMessage: string, startJob: () => Promise<void>) => {
      setStatus("running");
      setMessage(runningMessage);
      setJobId(jobId);
      setJobResult(null);
      setLoading(true);

      try {
        await startJob();
      } catch (e: unknown) {
        setStatus("error");
        const msg = e instanceof Error ? e.message : "ジョブの開始に失敗しました";
        setMessage(msg);
        setLoading(false);
        stopPolling();
        return;
      }

      setLoading(false);
    },
    []
  );

  const reset = useCallback(() => {
    stopPolling();
    setStatus("idle");
    setMessage("");
    setJobId(null);
    setJobResult(null);
    setLoading(false);
  }, []);

  return {
    status,
    message,
    jobId,
    jobResult,
    loading,
    runJob,
    reset,
  };
}
