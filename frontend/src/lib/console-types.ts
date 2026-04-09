export type ReviewStatus = "unhandled" | "investigating" | "confirmed_fraud" | "white";
export type AlertFilterStatus = ReviewStatus | "all";
export type RiskLevel = "low" | "medium" | "high" | "critical" | string;
export type AlertRiskFilter = RiskLevel | "all";

export type NamedEntity = {
  id: string;
  name: string;
};

export type EnvironmentSummary = {
  date: string | null;
  ipaddress: string | null;
  useragent: string | null;
};

export type DashboardResponse = {
  date: string;
  available_dates: string[];
  kpis: {
    fraud_rate: { value: number; unit: string };
    unhandled_alerts: { value: number; unit: string };
    estimated_damage: { value: number; unit: string };
  };
  trend: Array<{
    date: string;
    alerts: number;
  }>;
  case_ranking: Array<{
    case_key: string;
    risk_score: number;
    risk_level: RiskLevel;
    estimated_damage: number;
    affected_affiliate_count: number;
    latest_detected_at: string | null;
    primary_reason: string;
    status: ReviewStatus;
  }>;
  quality: {
    last_successful_ingest_at?: string | null;
    findings?: {
      findings_last_computed_at?: string | null;
      stale?: boolean;
      stale_reasons?: string[];
    };
    master_sync?: {
      last_synced_at?: string | null;
    };
  };
  job_status_summary: JobStatusResponse;
};

export type JobStatusResponse = {
  status: string;
  job_id?: string | null;
  message: string;
  started_at?: string | null;
  completed_at?: string | null;
  result?: Record<string, unknown> | null;
  queue?: {
    queued?: number;
    running?: number;
    failed?: number;
    succeeded?: number;
  } | null;
};

export type JobActionResponse = {
  success: boolean;
  message: string;
  details?: {
    job_id?: string;
    hours?: number;
    clicks?: boolean;
    conversions?: boolean;
  };
};

export type AlertListItem = {
  case_key: string;
  finding_key: string;
  environment: EnvironmentSummary;
  affected_affiliate_count: number;
  affected_affiliates: NamedEntity[];
  affected_program_count: number;
  affected_programs: NamedEntity[];
  risk_score: number;
  risk_level: RiskLevel;
  primary_reason: string;
  reasons: string[];
  status: ReviewStatus;
  reward_amount: number;
  reward_amount_source: string;
  reward_amount_is_estimated: boolean;
  transaction_count: number;
  latest_detected_at: string | null;
};

export type AlertsResponse = {
  available_dates: string[];
  applied_filters: {
    status: string;
    risk_level: string | null;
    start_date: string | null;
    end_date: string | null;
    search: string | null;
    sort: string;
  };
  status_counts: Record<ReviewStatus, number>;
  items: AlertListItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
};

export type AlertTransaction = {
  transaction_id: string;
  occurred_at: string | null;
  outcome_type: string;
  program_name: string;
  reward_amount: number;
  state: string;
  affiliate_id: string;
  affiliate_name: string;
};

export type AlertReviewHistoryItem = {
  status: ReviewStatus;
  reason: string;
  reviewed_by: string;
  reviewed_role: string;
  source_surface: string;
  request_id: string;
  finding_key_at_review?: string | null;
  reviewed_at: string | null;
};

export type AlertDetailResponse = {
  case_key: string;
  finding_key: string;
  environment: EnvironmentSummary;
  affected_affiliate_count: number;
  affected_affiliates: NamedEntity[];
  affected_program_count: number;
  affected_programs: NamedEntity[];
  risk_score: number;
  risk_level: RiskLevel;
  status: ReviewStatus;
  reward_amount: number;
  reward_amount_source: string;
  reward_amount_is_estimated: boolean;
  latest_detected_at: string | null;
  primary_reason: string;
  reasons: string[];
  evidence_transactions: AlertTransaction[];
  affiliate_recent_transactions: AlertTransaction[];
  review_history: AlertReviewHistoryItem[];
  actions: ReviewStatus[];
};

export type ReviewResponse = {
  requested_count: number;
  matched_current_count: number;
  updated_count: number;
  missing_keys: string[];
  status: ReviewStatus;
};
