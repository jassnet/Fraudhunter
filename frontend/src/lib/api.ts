// FastAPI Backend URL
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export async function fetchSummary(date?: string) {
  const url = date 
    ? `${API_BASE_URL}/api/summary?target_date=${date}`
    : `${API_BASE_URL}/api/summary`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch summary');
  return res.json();
}

export interface DailyStatsItem {
  date: string;
  clicks: number;
  conversions: number;
  suspicious_clicks: number;
  suspicious_conversions: number;
}

export async function fetchDailyStats(limit = 30): Promise<{ data: DailyStatsItem[] }> {
  const res = await fetch(`${API_BASE_URL}/api/stats/daily?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch daily stats');
  return res.json();
}

export interface SuspiciousResponse {
  date: string;
  data: SuspiciousItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface SuspiciousItem {
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
  risk_level?: "high" | "medium" | "low";
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

export async function fetchSuspiciousClicks(
  date?: string,
  limit = 500,
  offset = 0,
  search?: string
): Promise<SuspiciousResponse> {
  const params = new URLSearchParams();
  if (date) params.append('date', date);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());
  if (search) params.append('search', search);
  
  const res = await fetch(`${API_BASE_URL}/api/suspicious/clicks?${params}`);
  if (!res.ok) throw new Error('Failed to fetch suspicious clicks');
  return res.json();
}

export async function fetchSuspiciousConversions(
  date?: string,
  limit = 500,
  offset = 0,
  search?: string
): Promise<SuspiciousResponse> {
  const params = new URLSearchParams();
  if (date) params.append('date', date);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());
  if (search) params.append('search', search);
  
  const res = await fetch(`${API_BASE_URL}/api/suspicious/conversions?${params}`);
  if (!res.ok) throw new Error('Failed to fetch suspicious conversions');
  return res.json();
}

export async function syncMasters() {
  const res = await fetch(`${API_BASE_URL}/api/sync/masters`, {
    method: 'POST',
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to sync masters');
  }
  return res.json();
}

export interface MasterStatus {
  media_count: number;
  promotion_count: number;
  user_count: number;
  last_synced_at?: string | null;
}

export async function getMastersStatus(): Promise<MasterStatus> {
  const res = await fetch(`${API_BASE_URL}/api/masters/status`);
  if (!res.ok) throw new Error('Failed to get masters status');
  return res.json();
}

// Settings API
export interface Settings {
  click_threshold: number;
  media_threshold: number;
  program_threshold: number;
  burst_click_threshold: number;
  burst_window_seconds: number;
  conversion_threshold: number;
  conv_media_threshold: number;
  conv_program_threshold: number;
  burst_conversion_threshold: number;
  burst_conversion_window_seconds: number;
  min_click_to_conv_seconds: number;
  max_click_to_conv_seconds: number;
  browser_only: boolean;
  exclude_datacenter_ip: boolean;
}

export async function getSettings(): Promise<Settings> {
  const res = await fetch(`${API_BASE_URL}/api/settings`);
  if (!res.ok) throw new Error('Failed to get settings');
  return res.json();
}

export async function updateSettings(settings: Settings) {
  const res = await fetch(`${API_BASE_URL}/api/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to update settings');
  }
  return res.json();
}

export async function ingestClicks(date: string) {
  const res = await fetch(`${API_BASE_URL}/api/ingest/clicks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to start click ingestion');
  }
  return res.json();
}

export async function ingestConversions(date: string) {
  const res = await fetch(`${API_BASE_URL}/api/ingest/conversions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to start conversion ingestion');
  }
  return res.json();
}

export async function refreshData(hours = 24, clicks = true, conversions = true) {
  const res = await fetch(`${API_BASE_URL}/api/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hours, clicks, conversions }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to start refresh');
  }
  return res.json();
}

export async function getJobStatus() {
  const res = await fetch(`${API_BASE_URL}/api/job/status`);
  if (!res.ok) throw new Error('Failed to get job status');
  return res.json();
}

export async function getAvailableDates() {
  const res = await fetch(`${API_BASE_URL}/api/dates`);
  if (!res.ok) throw new Error('Failed to get dates');
  return res.json();
}

// Health check API
export interface HealthIssue {
  type: 'error' | 'warning';
  field: string;
  message: string;
  hint: string;
}

export interface HealthCheckResponse {
  status: 'ok' | 'warning' | 'error';
  issues: HealthIssue[];
  config: {
    db_path: string;
    acs_base_url: string;
    acs_auth: string;
  };
}

export async function getHealthStatus(): Promise<HealthCheckResponse> {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) throw new Error('Failed to get health status');
  return res.json();
}

