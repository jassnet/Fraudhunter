"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  type AdminActionType,
  type AdminCapabilityState,
  type AdminJobUiStatus,
  enqueueMasterSyncJob,
  enqueueRefreshJob,
  getAdminJobStatus,
  probeAdminCapabilities,
} from "@/lib/api";

interface UseAdminJobActionsOptions {
  onSuccess?: () => Promise<void> | void;
}

interface UseAdminJobActionsResult {
  capability: AdminCapabilityState;
  action: AdminActionType | null;
  status: AdminJobUiStatus;
  jobId: string | null;
  isBusy: boolean;
  runRefresh: () => Promise<void>;
  runMasterSync: () => Promise<void>;
}

const INITIAL_POLL_DELAY_MS = 600;
const POLL_INTERVAL_MS = 1500;

export function useAdminJobActions({
  onSuccess,
}: UseAdminJobActionsOptions = {}): UseAdminJobActionsResult {
  const [capability, setCapability] = useState<AdminCapabilityState>("unknown");
  const [action, setAction] = useState<AdminActionType | null>(null);
  const [status, setStatus] = useState<AdminJobUiStatus>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const successNotifiedRef = useRef(false);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      try {
        const canRun = await probeAdminCapabilities();
        if (!cancelled) {
          setCapability(canRun ? "available" : "unavailable");
        }
      } catch {
        if (!cancelled) {
          setCapability("unavailable");
        }
      }
    };

    void run();

    return () => {
      cancelled = true;
    };
  }, []);

  const completeSuccess = useCallback(async () => {
    setStatus("succeeded");
    stopPolling();
    if (!successNotifiedRef.current) {
      successNotifiedRef.current = true;
      await onSuccess?.();
    }
  }, [onSuccess, stopPolling]);

  const pollStatus = useCallback(async () => {
    try {
      const next = await getAdminJobStatus();
      if (next.job_id) {
        setJobId(next.job_id);
      }

      if (next.status === "running") {
        setStatus("running");
        return true;
      }
      if (next.status === "completed") {
        await completeSuccess();
        return false;
      }
      if (next.status === "failed") {
        setStatus("failed");
        stopPolling();
        return false;
      }

      return status === "queued";
    } catch {
      setStatus("failed");
      stopPolling();
      return false;
    }
  }, [completeSuccess, status, stopPolling]);

  useEffect(() => {
    if (status !== "queued" && status !== "running") {
      stopPolling();
      return;
    }

    let disposed = false;
    const tick = async () => {
      const shouldContinue = await pollStatus();
      if (!disposed && shouldContinue) {
        pollTimerRef.current = window.setTimeout(tick, POLL_INTERVAL_MS);
      }
    };

    pollTimerRef.current = window.setTimeout(tick, INITIAL_POLL_DELAY_MS);

    return () => {
      disposed = true;
      stopPolling();
    };
  }, [pollStatus, status, stopPolling]);

  const runAction = useCallback(
    async (
      nextAction: AdminActionType,
      submit: () => Promise<{ jobId: string | null }>
    ) => {
      successNotifiedRef.current = false;
      setAction(nextAction);
      setStatus("submitting");
      setJobId(null);
      stopPolling();

      try {
        const result = await submit();
        setJobId(result.jobId);
        setStatus("queued");
      } catch {
        setStatus("failed");
      }
    },
    [stopPolling]
  );

  const runRefresh = useCallback(async () => {
    await runAction("refresh", enqueueRefreshJob);
  }, [runAction]);

  const runMasterSync = useCallback(async () => {
    await runAction("master-sync", enqueueMasterSyncJob);
  }, [runAction]);

  const isBusy = useMemo(
    () => status === "submitting" || status === "queued" || status === "running",
    [status]
  );

  return {
    capability,
    action,
    status,
    jobId,
    isBusy,
    runRefresh,
    runMasterSync,
  };
}
