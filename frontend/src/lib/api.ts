// FastAPI Backend URL
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

type RetryOptions = {
  retries?: number;
  retryDelayMs?: number;
  retryOn?: (status: number) => boolean;
};

export class ApiError extends Error {
  status?: number;
  detail?: string;
}

const DEFAULT_RETRY_DELAY_MS = 500;
const defaultRetryOn = (status: number) =>
  status === 408 || status === 429 || (status >= 500 && status <= 599);

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function fetchJson<T>(
  url: string,
  init?: RequestInit,
  options: RetryOptions = {}
): Promise<T> {
  const { retries = 2, retryDelayMs = DEFAULT_RETRY_DELAY_MS, retryOn = defaultRetryOn } =
    options;
  let attempt = 0;

  while (true) {
    try {
      const res = await fetch(url, init);
      if (!res.ok) {
        let detail = "";
        try {
          const payload = await res.json();
          if (typeof payload === "string") {
            detail = payload;
          } else if (payload?.detail) {
            detail =
              typeof payload.detail === "string"
                ? payload.detail
                : JSON.stringify(payload.detail);
          } else if (payload?.message) {
            detail = payload.message;
          }
        } catch {
          detail = "";
        }

        const error = new ApiError(detail || `Request failed (${res.status})`);
        error.status = res.status;
        error.detail = detail;

        if (attempt < retries && retryOn(res.status)) {
          attempt += 1;
          await sleep(retryDelayMs * attempt);
          continue;
        }
        throw error;
      }

      return res.json();
    } catch (err) {
      const isAbortError = err instanceof DOMException && err.name === "AbortError";
      if (!isAbortError && attempt < retries) {
        attempt += 1;
        await sleep(retryDelayMs * attempt);
        continue;
      }
      throw err;
    }
  }
}

export function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError) {
    if (error.detail) return error.detail;
    if (error.message) return error.message;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export interface SummaryResponse {
  date: string;
  stats: {
    clicks: {
      total: number;
      unique_ips: number;
      media_count: number;
      prev_total: number;
    };
    conversions: {
      total: number;
      unique_ips: number;
      prev_total: number;
    };
    suspicious: {
      click_based: number;
      conversion_based: number;
    };
  };
  quality?: {
    last_successful_ingest_at?: string | null;
    click_ip_ua_coverage?: {
      total: number;
      missing: number;
      missing_rate: number;
    } | null;
    conversion_click_enrichment?: {
      total: number;
      enriched: number;
      success_rate: number;
    } | null;
    master_sync?: {
      last_synced_at?: string | null;
    } | null;
  };
}

export async function fetchSummary(date?: string): Promise<SummaryResponse> {
  const url = date
    ? `${API_BASE_URL}/api/summary?target_date=${date}`
    : `${API_BASE_URL}/api/summary`;
  return fetchJson<SummaryResponse>(url);
}

export interface DailyStatsItem {
  date: string;
  clicks: number;
  conversions: number;
  suspicious_clicks: number;
  suspicious_conversions: number;
}

export async function fetchDailyStats(limit = 30): Promise<{ data: DailyStatsItem[] }> {
  return fetchJson(`${API_BASE_URL}/api/stats/daily?limit=${limit}`);
}

export type SuspiciousRiskLevel = "high" | "medium" | "low";
export type SuspiciousSortBy = "count" | "risk" | "latest";
export type SuspiciousSortOrder = "asc" | "desc";

export interface SuspiciousResponse {
  date: string;
  data: SuspiciousItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface SuspiciousItem {
  finding_key?: string;
  date: string;
  ipaddress: string;
  useragent: string;
  total_clicks?: number;
  total_conversions?: number;
  media_count: number;
  program_count: number;
  first_time: string;
  last_time: string;
  reasons: string[];
  reasons_formatted: string[];
  min_click_to_conv_seconds?: number | null;
  max_click_to_conv_seconds?: number | null;
  media_names?: string[];
  program_names?: string[];
  affiliate_names?: string[];
  risk_level?: SuspiciousRiskLevel;
  risk_score?: number;
  risk_label?: string;
  details?: {
    media_id: string;
    program_id: string;
    click_count?: number;
    conversion_count?: number;
    media_name: string;
    program_name: string;
    affiliate_name?: string;
  }[];
}

export interface SuspiciousQueryOptions {
  search?: string;
  riskLevel?: SuspiciousRiskLevel;
  sortBy?: SuspiciousSortBy;
  sortOrder?: SuspiciousSortOrder;
  includeDetails?: boolean;
}

function appendSuspiciousParams(
  params: URLSearchParams,
  options?: SuspiciousQueryOptions
) {
  if (!options) {
    return;
  }
  if (options.search) params.append("search", options.search);
  if (options.riskLevel) params.append("risk_level", options.riskLevel);
  if (options.sortBy) params.append("sort_by", options.sortBy);
  if (options.sortOrder) params.append("sort_order", options.sortOrder);
  if (typeof options.includeDetails === "boolean") {
    params.append("include_details", String(options.includeDetails));
  }
}

export async function fetchSuspiciousClicks(
  date?: string,
  limit = 500,
  offset = 0,
  options?: SuspiciousQueryOptions
): Promise<SuspiciousResponse> {
  const params = new URLSearchParams();
  if (date) params.append("date", date);
  params.append("limit", limit.toString());
  params.append("offset", offset.toString());
  appendSuspiciousParams(params, options);

  return fetchJson(`${API_BASE_URL}/api/suspicious/clicks?${params}`);
}

export async function fetchSuspiciousConversions(
  date?: string,
  limit = 500,
  offset = 0,
  options?: SuspiciousQueryOptions
): Promise<SuspiciousResponse> {
  const params = new URLSearchParams();
  if (date) params.append("date", date);
  params.append("limit", limit.toString());
  params.append("offset", offset.toString());
  appendSuspiciousParams(params, options);

  return fetchJson(`${API_BASE_URL}/api/suspicious/conversions?${params}`);
}

export async function fetchSuspiciousClickDetail(
  findingKey: string
): Promise<SuspiciousItem> {
  return fetchJson(`${API_BASE_URL}/api/suspicious/clicks/${findingKey}`);
}

export async function fetchSuspiciousConversionDetail(
  findingKey: string
): Promise<SuspiciousItem> {
  return fetchJson(`${API_BASE_URL}/api/suspicious/conversions/${findingKey}`);
}

export interface AvailableDatesResponse {
  dates: string[];
}

export async function getAvailableDates(): Promise<AvailableDatesResponse> {
  return fetchJson<AvailableDatesResponse>(`${API_BASE_URL}/api/dates`);
}

export interface JobStatusResponse {
  status: string;
  job_id?: string | null;
  message?: string;
  started_at?: string | null;
  completed_at?: string | null;
  result?: Record<string, unknown> | null;
}

export async function getJobStatus(): Promise<JobStatusResponse> {
  return fetchJson<JobStatusResponse>(`${API_BASE_URL}/api/job/status`);
}
