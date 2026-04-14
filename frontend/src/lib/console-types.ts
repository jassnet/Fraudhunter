export type ReviewStatus = "unhandled" | "investigating" | "confirmed_fraud" | "white";
export type AlertFilterStatus = ReviewStatus | "all";
export type RiskLevel = "low" | "medium" | "high";
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

export type CaseAssignee = {
  user_id: string;
  assigned_by?: string | null;
  assigned_at: string | null;
  updated_at?: string | null;
};

export type FollowUpTask = {
  id: string;
  task_type: string;
  label: string;
  status: "open" | "completed" | "cancelled" | string;
  created_by: string;
  created_at: string | null;
  due_at?: string | null;
  is_overdue?: boolean;
  completed_by?: string | null;
  completed_at?: string | null;
};

export type RelatedCaseSummary = {
  case_key: string;
  display_label: string;
  secondary_label: string;
  status: ReviewStatus;
  risk_score: number;
  risk_level: RiskLevel;
  latest_detected_at: string | null;
};

export type DashboardResponse = {
  date: string;
  target_date: string;
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
    display_label: string;
    secondary_label: string;
    risk_score: number;
    risk_level: RiskLevel;
    priority_score: number;
    estimated_damage: number;
    affected_affiliate_count: number;
    latest_detected_at: string | null;
    primary_reason: string;
    status: ReviewStatus;
    assignee?: CaseAssignee | null;
    follow_up_open_count?: number;
  }>;
  review_outcomes: {
    confirmed_fraud: number;
    white: number;
    investigating: number;
    reviewed_total: number;
    confirmed_ratio: number | null;
  };
  operations: {
    oldest_unhandled_days: number | null;
    stale_unhandled_count: number;
    failed_jobs: Array<{
      job_id: string;
      job_type: string;
      message: string | null;
      error_message: string | null;
      finished_at: string | null;
    }>;
    schedules: Array<{
      key: string;
      label: string;
      description: string;
      next_run_at: string | null;
    }>;
  };
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
    retry_scheduled?: number;
    running?: number;
    failed?: number;
    oldest_queued_at?: string | null;
    oldest_queued_age_seconds?: number | null;
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
  display_label: string;
  secondary_label: string;
  assignee?: CaseAssignee | null;
  follow_up_open_count?: number;
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
  state_raw?: string | null;
  affiliate_id: string;
  affiliate_name: string;
};

export type AlertReviewHistoryItem = {
  status: ReviewStatus;
  reason: string;
  reviewed_by: string;
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
  affiliate_recent_scope?: NamedEntity | null;
  review_history: AlertReviewHistoryItem[];
  assignee?: CaseAssignee | null;
  follow_up_tasks: FollowUpTask[];
  related_cases: RelatedCaseSummary[];
  actions: ReviewStatus[];
};

export type ReviewResponse = {
  requested_count: number;
  matched_current_count: number;
  updated_count: number;
  missing_keys: string[];
  status: ReviewStatus;
};

export type AssignmentResponse = {
  updated_count: number;
  action: "claim" | "release" | string;
};

export type FollowUpTaskUpdateResponse = FollowUpTask;

export type ConsoleSettings = {
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
  fraud_check_min_total: number;
  fraud_check_invalid_rate: number;
  fraud_check_duplicate_plid_count: number;
  fraud_check_duplicate_plid_rate: number;
  fraud_track_min_total: number;
  fraud_track_auth_error_rate: number;
  fraud_track_auth_ip_ua_rate: number;
  fraud_action_min_total: number;
  fraud_action_short_gap_seconds: number;
  fraud_action_short_gap_count: number;
  fraud_action_cancel_rate: number;
  fraud_action_fixed_gap_min_count: number;
  fraud_action_fixed_gap_max_unique: number;
  fraud_spike_multiplier: number;
  fraud_spike_lookback_days: number;
  browser_only: boolean;
  exclude_datacenter_ip: boolean;
};

export type ConsoleSettingsUpdateResponse = {
  success: boolean;
  settings: ConsoleSettings;
  persisted: boolean;
  warning?: string;
  settings_version_id?: string;
  settings_fingerprint?: string;
  findings_recomputed?: boolean;
  findings_recompute_enqueued?: boolean;
  recompute_job_ids?: string[];
  recompute_target_dates?: string[];
  generation_id?: string;
};
