import { ApiError, fetchJson } from "./core";

export interface JobStatusResponse {
  status: string;
  job_id?: string | null;
  message?: string;
  started_at?: string | null;
  completed_at?: string | null;
  result?: Record<string, unknown> | null;
  queue?: Record<string, unknown> | null;
}

export type AdminCapabilityState = "unknown" | "available" | "unavailable";
export type AdminActionType = "refresh" | "master-sync";
export type AdminJobUiStatus =
  | "idle"
  | "submitting"
  | "queued"
  | "running"
  | "succeeded"
  | "failed";

interface IngestResponse {
  success: boolean;
  message?: string;
  details?: {
    job_id?: string | null;
  };
}

const ADMIN_API_BASE = "/api/admin";
export const ADMIN_REFRESH_LOOKBACK_HOURS = 24;

async function fetchAdminJson<T>(path: string, init?: RequestInit) {
  return fetchJson<T>(`${ADMIN_API_BASE}${path}`, init, {
    retries: 0,
    retryOn: () => false,
  });
}

function getConflictJobId(payload: unknown): string | null {
  if (typeof payload !== "object" || payload === null) {
    return null;
  }
  if (!("details" in payload) || typeof payload.details !== "object" || payload.details === null) {
    return null;
  }
  return "job_id" in payload.details ? (payload.details.job_id as string | null | undefined) ?? null : null;
}

export async function getJobStatus(): Promise<JobStatusResponse> {
  return fetchJson<JobStatusResponse>(`/api/job/status`);
}

export async function getAdminJobStatus(): Promise<JobStatusResponse> {
  return fetchAdminJson<JobStatusResponse>("/job-status");
}

export async function probeAdminCapabilities(): Promise<boolean> {
  try {
    await getAdminJobStatus();
    return true;
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return false;
    }
    throw error;
  }
}

export async function enqueueRefreshJob(): Promise<{ jobId: string | null }> {
  try {
    const response = await fetchAdminJson<IngestResponse>("/refresh", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        hours: ADMIN_REFRESH_LOOKBACK_HOURS,
        clicks: true,
        conversions: true,
        detect: true,
      }),
    });
    return { jobId: response.details?.job_id ?? null };
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      const jobId = getConflictJobId(error.payload);
      if (jobId) {
        return { jobId };
      }
    }
    throw error;
  }
}

export async function enqueueMasterSyncJob(): Promise<{ jobId: string | null }> {
  try {
    const response = await fetchAdminJson<IngestResponse>("/master-sync", {
      method: "POST",
    });
    return { jobId: response.details?.job_id ?? null };
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      const jobId = getConflictJobId(error.payload);
      if (jobId) {
        return { jobId };
      }
    }
    throw error;
  }
}
