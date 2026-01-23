"use client";

import { useEffect, useRef } from "react";
import { useJobStatus } from "@/hooks/use-job-status";
import { useNotifications } from "@/components/notification-center";

export function JobStatusNotifier() {
  const { jobState } = useJobStatus();
  const { notify } = useNotifications();
  const previousStatus = useRef<string | null>(null);
  const previousJobId = useRef<string | null>(null);

  useEffect(() => {
    if (!jobState) return;

    const currentStatus = jobState.status;
    const currentJobId = jobState.job_id ?? null;
    const shouldNotifyCompletion =
      previousStatus.current === "running" &&
      currentStatus === "completed" &&
      previousJobId.current === currentJobId;
    const shouldNotifyFailure =
      previousStatus.current === "running" &&
      currentStatus === "failed" &&
      previousJobId.current === currentJobId;

    if (shouldNotifyCompletion) {
      notify({
        title: "バックグラウンド処理が完了しました",
        description: jobState.message || "処理が正常に終了しました。",
        variant: "success",
        duration: null,
      });
    }

    if (shouldNotifyFailure) {
      notify({
        title: "バックグラウンド処理が失敗しました",
        description: jobState.message || "処理に失敗しました。ログを確認してください。",
        variant: "error",
        duration: null,
      });
    }

    previousStatus.current = currentStatus;
    previousJobId.current = currentJobId;
  }, [jobState, notify]);

  return null;
}
