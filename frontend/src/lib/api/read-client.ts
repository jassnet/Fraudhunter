import { API_BASE_URL, fetchJson } from "./core";

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
    findings?: {
      findings_last_computed_at?: string | null;
      stale?: boolean;
      stale_reasons?: string[];
      click_findings_last_computed_at?: string | null;
      conversion_findings_last_computed_at?: string | null;
    } | null;
    master_sync?: {
      last_synced_at?: string | null;
    } | null;
  };
}

export interface DailyStatsItem {
  date: string;
  clicks: number;
  conversions: number;
  suspicious_clicks: number;
  suspicious_conversions: number;
}

export type SuspiciousRiskLevel = "high" | "medium" | "low";
export type SuspiciousSortBy = "count" | "risk" | "latest";
export type SuspiciousSortOrder = "asc" | "desc";

export interface SuspiciousItem {
  finding_key?: string;
  date: string;
  ipaddress: string;
  useragent: string;
  ipaddress_masked?: string;
  useragent_masked?: string;
  sensitive_values_masked?: boolean;
  total_clicks?: number;
  total_conversions?: number;
  media_count: number;
  program_count: number;
  first_time: string;
  last_time: string;
  reasons: string[];
  reasons_formatted: string[];
  reason_summary?: string | null;
  reason_group_count?: number;
  reason_groups?: string[];
  /** 同一検知パターン（理由カテゴリの組み合わせ）で一覧を束ねるためのキー */
  reason_cluster_key?: string;
  min_click_to_conv_seconds?: number | null;
  max_click_to_conv_seconds?: number | null;
  linked_click_count?: number | null;
  linked_clicks_per_conversion?: number | null;
  extra_window_click_count?: number | null;
  extra_window_non_browser_ratio?: number | null;
  media_names?: string[];
  program_names?: string[];
  affiliate_names?: string[];
  risk_level?: SuspiciousRiskLevel;
  risk_score?: number;
  risk_label?: string;
  evidence_status?: "available" | "expired" | "unknown";
  evidence_available?: boolean;
  evidence_expired?: boolean;
  evidence_retention_days?: number | null;
  evidence_expires_on?: string | null;
  evidence_checked_on?: string | null;
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

export interface SuspiciousResponse {
  date: string;
  data: SuspiciousItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface SuspiciousQueryOptions {
  search?: string;
  riskLevel?: SuspiciousRiskLevel;
  sortBy?: SuspiciousSortBy;
  sortOrder?: SuspiciousSortOrder;
  includeDetails?: boolean;
  maskSensitive?: boolean;
}

export interface AvailableDatesResponse {
  dates: string[];
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
  if (typeof options.maskSensitive === "boolean") {
    params.append("mask_sensitive", String(options.maskSensitive));
  }
}

export async function fetchSummary(date?: string): Promise<SummaryResponse> {
  const url = date
    ? `${API_BASE_URL}/api/summary?target_date=${date}`
    : `${API_BASE_URL}/api/summary`;
  return fetchJson<SummaryResponse>(url);
}

export async function fetchDailyStats(
  limit = 30,
  targetDate?: string
): Promise<{ data: DailyStatsItem[] }> {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  if (targetDate) params.set("target_date", targetDate);
  return fetchJson(`${API_BASE_URL}/api/stats/daily?${params.toString()}`);
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

export async function getAvailableDates(): Promise<AvailableDatesResponse> {
  return fetchJson<AvailableDatesResponse>(`${API_BASE_URL}/api/dates`);
}
