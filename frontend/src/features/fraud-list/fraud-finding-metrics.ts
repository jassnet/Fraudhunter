"use client";

import type { FraudFindingItem } from "@/lib/api";

type FraudMetricFormat = "number" | "percent" | "seconds";

interface FraudMetricDefinition {
  key: string;
  label: string;
  format?: FraudMetricFormat;
}

export interface FraudDetailMetric {
  key: string;
  label: string;
  value: string;
}

const FRAUD_METRIC_DEFINITIONS: readonly FraudMetricDefinition[] = [
  { key: "action_total", label: "アクション件数" },
  { key: "action_cancel_count", label: "キャンセル件数" },
  { key: "action_cancel_rate", label: "キャンセル率", format: "percent" },
  { key: "action_short_gap_count", label: "短時間CV件数" },
  { key: "action_fixed_gap_unique_count", label: "固定間隔CV件数" },
  { key: "check_total", label: "審査件数" },
  { key: "check_invalid_count", label: "審査NG件数" },
  { key: "check_invalid_rate", label: "審査NG率", format: "percent" },
  { key: "check_duplicate_plid_count", label: "重複PLID件数" },
  { key: "check_duplicate_plid_rate", label: "重複PLID率", format: "percent" },
  { key: "track_total", label: "トラッキング件数" },
  { key: "track_auth_error_count", label: "認証エラー件数" },
  { key: "track_auth_error_rate", label: "認証エラー率", format: "percent" },
  { key: "track_auth_ip_ua_count", label: "認証IP/UA一致件数" },
  { key: "track_auth_ip_ua_rate", label: "認証IP/UA一致率", format: "percent" },
  { key: "click_count", label: "クリック件数" },
  { key: "access_count", label: "アクセス件数" },
  { key: "imp_count", label: "インプレッション件数" },
  { key: "ctr", label: "CTR", format: "percent" },
  { key: "min_click_to_conv_seconds", label: "最短クリック間隔", format: "seconds" },
  { key: "max_click_to_conv_seconds", label: "最長クリック間隔", format: "seconds" },
];

function formatMetricValue(value: unknown, format: FraudMetricFormat = "number") {
  if (typeof value !== "number") {
    return typeof value === "string" && value.trim() ? value : "-";
  }

  if (format === "percent") {
    return value.toLocaleString("ja-JP", {
      style: "percent",
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    });
  }

  if (format === "seconds") {
    return `${Math.round(value).toLocaleString("ja-JP")}秒`;
  }

  return value.toLocaleString("ja-JP", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
}

export function buildFraudDetailMetrics(details?: FraudFindingItem["details"]): FraudDetailMetric[] {
  if (!details) {
    return [];
  }

  return FRAUD_METRIC_DEFINITIONS.flatMap(({ key, label, format }) =>
    key in details ? [{ key, label, value: formatMetricValue(details[key], format) }] : []
  );
}

export function getFraudReasonSummary(item: FraudFindingItem) {
  return item.reason_summary?.trim() || item.reasons_formatted?.[0] || item.reasons?.[0] || "-";
}
