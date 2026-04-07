export type ReviewStatus = "unhandled" | "investigating" | "confirmed_fraud" | "white";
export type AlertFilterStatus = ReviewStatus | "all";
export type RiskLevel = "low" | "medium" | "high" | "critical" | string;

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
  ranking: Array<{
    affiliate_id: string;
    affiliate_name: string;
    fraud_rate: number;
    alert_count: number;
    total_conversions: number;
    estimated_damage: number;
  }>;
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
  finding_key: string;
  detected_at: string;
  affiliate_id: string;
  affiliate_name: string;
  outcome_type: string;
  risk_score: number;
  risk_level: RiskLevel;
  pattern: string;
  status: ReviewStatus;
  reward_amount: number;
  transaction_count: number;
};

export type AlertsResponse = {
  available_dates: string[];
  applied_filters: {
    status: string;
    start_date: string | null;
    end_date: string | null;
    sort: string;
  };
  status_counts: Record<ReviewStatus, number>;
  items: AlertListItem[];
  total: number;
};

export type AlertTransaction = {
  transaction_id: string;
  occurred_at: string;
  outcome_type: string;
  reward_amount: number;
  state: string;
};

export type AlertDetailResponse = {
  finding_key: string;
  affiliate_id: string;
  affiliate_name: string;
  risk_score: number;
  risk_level: RiskLevel;
  status: ReviewStatus;
  reward_amount: number;
  detected_at: string;
  outcome_type: string;
  program_name: string | null;
  reasons: string[];
  transactions: AlertTransaction[];
  actions: ReviewStatus[];
};

export type ReviewResponse = {
  updated_count: number;
  status: ReviewStatus;
};
