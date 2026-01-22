"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getJobStatus, JobStatusResponse } from "@/lib/api";

type RunnerStatus = "idle" | "running" | "success" | "error";

type JobResult = {
  clicks?: { new: number; skipped: number; valid_entry?: number };
  conversions?: { new: number; skipped: number; valid_entry?: number };
  count?: number;
  total?: number;
  [key: string]: unknown;
} | null;

type JobStatusResponseWithResult = JobStatusResponse & { result?: JobResult };

export function useJobRunner(onSuccess?: () => void) {
  const [status, setStatus] = useState<RunnerStatus>("idle");
  const [message, setMessage] = useState<string>("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobResult, setJobResult] = useState<JobResult>(null);
  const [loading, setLoading] = useState(false);

  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMounted = useRef(true);
  const pollJobStatusRef = useRef<(expectedJobId?: string) => void>(() => {});

  const clearTimer = () => {
    if (pollTimer.current) {
      clearTimeout(pollTimer.current);
      pollTimer.current = null;
    }
  };

  const pollJobStatus = useCallback(
    async (expectedJobId?: string) => {
      try {
        const res: JobStatusResponseWithResult = await getJobStatus();
        const currentId = res.job_id ?? expectedJobId ?? null;
        if (!isMounted.current) return;

        setJobId(currentId);
        setMessage(res.message || "");

        if (res.status === "running") {
          setStatus("running");
          setLoading(true);
          pollTimer.current = setTimeout(() => pollJobStatusRef.current(expectedJobId), 2000);
          return;
        }

        if (res.status === "completed") {
          setStatus("success");
          setJobResult(res.result ?? null);
          setLoading(false);
          onSuccess?.();
          return;
        }

        if (res.status === "failed") {
          setStatus("error");
          setJobResult(res.result ?? null);
          setLoading(false);
          return;
        }

        // idle or unknown
        setStatus("idle");
        setLoading(false);
      } catch (err) {
        if (!isMounted.current) return;
        const errorMessage =
          err instanceof Error ? err.message : "ジョブの状態取得に失敗しました";
        setStatus("error");
        setMessage(errorMessage);
        setLoading(false);
      }
    },
    [onSuccess]
  );


  useEffect(() => {
    pollJobStatusRef.current = pollJobStatus;
  }, [pollJobStatus]);

  const runJob = useCallback(
    async (id: string, startMessage: string, jobFn: () => Promise<unknown>) => {
      if (loading) return;
      clearTimer();
      setStatus("running");
      setMessage(startMessage);
      setJobId(id);
      setJobResult(null);
      setLoading(true);

      try {
        await jobFn();
        // 少し待ってからポーリング開始
        pollTimer.current = setTimeout(() => pollJobStatusRef.current(id), 500);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "ジョブの開始に失敗しました";
        setStatus("error");
        setMessage(errorMessage);
        setLoading(false);
      }
    },
    [loading]
  );

  const reset = useCallback(() => {
    clearTimer();
    setStatus("idle");
    setMessage("");
    setJobId(null);
    setJobResult(null);
    setLoading(false);
  }, []);

  useEffect(() => {
    return () => {
      isMounted.current = false;
      clearTimer();
    };
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
