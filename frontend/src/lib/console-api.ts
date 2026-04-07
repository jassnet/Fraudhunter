import type {
  AlertDetailResponse,
  AlertFilterStatus,
  AlertsResponse,
  DashboardResponse,
  JobActionResponse,
  ReviewResponse,
  ReviewStatus,
} from "@/lib/console-types";

type AlertQuery = {
  status: AlertFilterStatus;
  startDate?: string;
  endDate?: string;
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
      throw new Error("通信に失敗しました。");
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

export function getDashboard() {
  return fetchJson<DashboardResponse>("/api/console/dashboard");
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

export function getAlerts(query: AlertQuery) {
  const searchParams = new URLSearchParams({
    status: query.status,
    sort: query.sort ?? "risk_desc",
  });
  if (query.startDate) {
    searchParams.set("start_date", query.startDate);
  }
  if (query.endDate) {
    searchParams.set("end_date", query.endDate);
  }
  if (query.page) {
    searchParams.set("page", String(query.page));
  }
  if (query.pageSize) {
    searchParams.set("page_size", String(query.pageSize));
  }
  return fetchJson<AlertsResponse>(`/api/console/alerts?${searchParams.toString()}`);
}

export function getAlertDetail(findingKey: string) {
  return fetchJson<AlertDetailResponse>(`/api/console/alerts/${encodeURIComponent(findingKey)}`);
}

export function reviewAlerts(findingKeys: string[], status: ReviewStatus) {
  return fetchJson<ReviewResponse>("/api/console/alerts/review", {
    method: "POST",
    body: JSON.stringify({
      finding_keys: findingKeys,
      status,
    }),
  });
}
