import type {
  AlertDetailResponse,
  AlertFilterStatus,
  AlertsResponse,
  AssignmentResponse,
  ConsoleSettings,
  ConsoleSettingsUpdateResponse,
  DashboardResponse,
  FollowUpTaskUpdateResponse,
  JobActionResponse,
  JobStatusResponse,
  ReviewResponse,
  ReviewStatus,
} from "@/lib/console-types";

type AlertQuery = {
  status: AlertFilterStatus;
  riskLevel?: string;
  startDate?: string;
  endDate?: string;
  search?: string;
  sort?: string;
  page?: number;
  pageSize?: number;
};

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
    cache: "no-store",
  });
  const raw = await response.text();

  if (!response.ok) {
    if (!raw) {
      throw new Error("リクエストに失敗しました。");
    }

    let message = raw;
    try {
      const parsed = JSON.parse(raw) as { detail?: string };
      message = parsed.detail || raw;
    } catch {
      // Fall back to the raw response body.
    }
    throw new Error(message);
  }

  return (raw ? JSON.parse(raw) : {}) as T;
}

export function getDashboard(targetDate?: string) {
  const searchParams = new URLSearchParams();
  if (targetDate) {
    searchParams.set("target_date", targetDate);
  }
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return fetchJson<DashboardResponse>(`/api/console/dashboard${suffix}`);
}

export function refreshLatestData() {
  return fetchJson<JobActionResponse>("/api/console/refresh", {
    method: "POST",
    body: JSON.stringify({
      hours: 1,
      clicks: true,
      conversions: true,
      detect: true,
    }),
  });
}

export function syncMasterData() {
  return fetchJson<JobActionResponse>("/api/console/sync/masters", {
    method: "POST",
  });
}

export function getJobStatus(jobId: string) {
  return fetchJson<JobStatusResponse>(`/api/console/job-status/${encodeURIComponent(jobId)}`);
}

export function getAlerts(query: AlertQuery) {
  const searchParams = new URLSearchParams({
    status: query.status,
    sort: query.sort ?? "risk_desc",
  });
  if (query.riskLevel) {
    searchParams.set("risk_level", query.riskLevel);
  }
  if (query.startDate) {
    searchParams.set("start_date", query.startDate);
  }
  if (query.endDate) {
    searchParams.set("end_date", query.endDate);
  }
  if (query.search) {
    searchParams.set("search", query.search);
  }
  if (query.page) {
    searchParams.set("page", String(query.page));
  }
  if (query.pageSize) {
    searchParams.set("page_size", String(query.pageSize));
  }
  return fetchJson<AlertsResponse>(`/api/console/alerts?${searchParams.toString()}`);
}

export function buildAlertsCsvUrl(query: AlertQuery) {
  const searchParams = new URLSearchParams({
    status: query.status,
    sort: query.sort ?? "risk_desc",
  });
  if (query.riskLevel) {
    searchParams.set("risk_level", query.riskLevel);
  }
  if (query.startDate) {
    searchParams.set("start_date", query.startDate);
  }
  if (query.endDate) {
    searchParams.set("end_date", query.endDate);
  }
  if (query.search) {
    searchParams.set("search", query.search);
  }
  return `/api/console/alerts/export?${searchParams.toString()}`;
}

export function getAlertDetail(caseKey: string) {
  return fetchJson<AlertDetailResponse>(`/api/console/alerts/${encodeURIComponent(caseKey)}`);
}

export function reviewAlerts(caseKeys: string[], status: ReviewStatus, reason: string) {
  return fetchJson<ReviewResponse>("/api/console/alerts/review", {
    method: "POST",
    body: JSON.stringify({
      case_keys: caseKeys,
      status,
      reason,
    }),
  });
}

export function reviewAlertsByFilter(
  filters: Omit<AlertQuery, "page" | "pageSize">,
  status: ReviewStatus,
  reason: string,
) {
  return fetchJson<ReviewResponse>("/api/console/alerts/review", {
    method: "POST",
    body: JSON.stringify({
      case_keys: [],
      status,
      reason,
      filters: {
        status: filters.status,
        risk_level: filters.riskLevel,
        start_date: filters.startDate,
        end_date: filters.endDate,
        search: filters.search,
        sort: filters.sort ?? "risk_desc",
      },
    }),
  });
}

export function assignAlerts(caseKeys: string[], action: "claim" | "release") {
  return fetchJson<AssignmentResponse>("/api/console/alerts/assign", {
    method: "POST",
    body: JSON.stringify({
      case_keys: caseKeys,
      action,
    }),
  });
}

export function updateFollowUpTask(taskId: string, status: "open" | "completed") {
  return fetchJson<FollowUpTaskUpdateResponse>("/api/console/alerts/follow-up", {
    method: "POST",
    body: JSON.stringify({
      task_id: taskId,
      status,
    }),
  });
}

export function getConsoleSettings() {
  return fetchJson<ConsoleSettings>("/api/console/settings");
}

export function updateConsoleSettings(settings: ConsoleSettings) {
  return fetchJson<ConsoleSettingsUpdateResponse>("/api/console/settings", {
    method: "POST",
    body: JSON.stringify(settings),
  });
}
