"use client";

import { Button } from "@/components/ui/button";
import { fraudCopy } from "@/features/fraud-list/copy";
import type { FraudFindingDetailStatus } from "@/features/fraud-list/use-fraud-finding-details";
import type { FraudFindingItem } from "@/lib/api";
import { cn } from "@/lib/utils";

interface FraudFindingDetailPanelProps {
  className?: string;
  item: FraudFindingItem | null;
  message: string | null;
  onClose?: () => void;
  status: FraudFindingDetailStatus;
}

const DETAIL_LABELS: Record<string, string> = {
  check_total: "審査件数",
  check_invalid_count: "審査NG件数",
  check_invalid_rate: "審査NG率",
  check_duplicate_plid_count: "重複PLID件数",
  check_duplicate_plid_rate: "重複PLID率",
  track_total: "トラッキング件数",
  track_auth_error_count: "認証エラー件数",
  track_auth_error_rate: "認証エラー率",
  track_auth_ip_ua_count: "認証IP/UA一致件数",
  track_auth_ip_ua_rate: "認証IP/UA一致率",
  action_total: "アクション件数",
  action_cancel_count: "キャンセル件数",
  action_cancel_rate: "キャンセル率",
  action_short_gap_count: "短時間CV件数",
  action_fixed_gap_unique_count: "固定間隔CV件数",
  min_click_to_conv_seconds: "最短クリック間隔",
  max_click_to_conv_seconds: "最長クリック間隔",
  click_count: "クリック件数",
  access_count: "アクセス件数",
  imp_count: "インプレッション件数",
  ctr: "CTR",
};

const RATE_KEYS = new Set([
  "check_invalid_rate",
  "check_duplicate_plid_rate",
  "track_auth_error_rate",
  "track_auth_ip_ua_rate",
  "action_cancel_rate",
  "ctr",
]);

const SECOND_KEYS = new Set(["min_click_to_conv_seconds", "max_click_to_conv_seconds"]);

const DETAIL_KEY_ORDER = [
  "action_total",
  "action_cancel_count",
  "action_cancel_rate",
  "action_short_gap_count",
  "action_fixed_gap_unique_count",
  "check_total",
  "check_invalid_count",
  "check_invalid_rate",
  "check_duplicate_plid_count",
  "check_duplicate_plid_rate",
  "track_total",
  "track_auth_error_count",
  "track_auth_error_rate",
  "track_auth_ip_ua_count",
  "track_auth_ip_ua_rate",
  "click_count",
  "access_count",
  "imp_count",
  "ctr",
  "min_click_to_conv_seconds",
  "max_click_to_conv_seconds",
] as const;

function SelectedDetailValue({ value }: { value?: string | null }) {
  return <div>{value?.trim() ? value : "-"}</div>;
}

function formatDetailValue(key: string, value: unknown) {
  if (typeof value === "number") {
    if (RATE_KEYS.has(key)) {
      return value.toLocaleString("ja-JP", {
        style: "percent",
        minimumFractionDigits: 0,
        maximumFractionDigits: 1,
      });
    }
    if (SECOND_KEYS.has(key)) {
      return `${Math.round(value).toLocaleString("ja-JP")}秒`;
    }
    return value.toLocaleString("ja-JP", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  }

  return typeof value === "string" && value.trim() ? value : "-";
}

export function FraudFindingDetailPanel({
  className,
  item,
  message,
  onClose,
  status,
}: FraudFindingDetailPanelProps) {
  const detailMetrics = item?.details
    ? DETAIL_KEY_ORDER.flatMap((key) =>
        key in item.details!
          ? [{ key, label: DETAIL_LABELS[key], value: formatDetailValue(key, item.details![key]) }]
          : []
      )
    : [];

  return (
    <aside
      className={cn(
        "fc-surface-card-soft min-w-0 p-4",
        className
      )}
    >
      <div className="mb-4 flex items-start justify-between gap-3 border-b border-border/70 pb-3">
        <div className="min-w-0">
          <div className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
            {fraudCopy.labels.detailPanelTitle}
          </div>
          <div className="mt-1 text-sm text-foreground/80">
            {item ? fraudCopy.labels.detail : fraudCopy.labels.detailPlaceholder}
          </div>
        </div>
        {onClose ? (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={onClose}
            className="h-8 shrink-0 px-2 text-xs text-muted-foreground hover:text-foreground"
          >
            {fraudCopy.labels.closeDetail}
          </Button>
        ) : null}
      </div>

      {!item ? (
        <div className="text-sm text-muted-foreground">{fraudCopy.labels.detailPlaceholder}</div>
      ) : status === "loading" ? (
        <div className="text-sm text-muted-foreground">{fraudCopy.states.loadingRange}</div>
      ) : status === "error" ? (
        <div className="space-y-2 text-sm">
          <div className="font-medium text-destructive">{fraudCopy.states.detailError}</div>
          <div className="text-muted-foreground">{message || fraudCopy.states.detailError}</div>
        </div>
      ) : (
        <div className="space-y-3 text-sm">
          <div>
            <div className="text-xs text-muted-foreground">{fraudCopy.labels.user}</div>
            <SelectedDetailValue value={item.user_name} />
          </div>
          <div>
            <div className="text-xs text-muted-foreground">{fraudCopy.labels.media}</div>
            <SelectedDetailValue value={item.media_name} />
          </div>
          <div>
            <div className="text-xs text-muted-foreground">{fraudCopy.labels.promotion}</div>
            <SelectedDetailValue value={item.promotion_name} />
          </div>
          <div>
            <div className="text-xs text-muted-foreground">{fraudCopy.labels.reasons}</div>
            <ul className="list-disc pl-5">
              {(item.reasons_formatted || []).map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
          <div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <div className="text-xs text-muted-foreground">{fraudCopy.labels.firstDetected}</div>
                <SelectedDetailValue value={item.first_time} />
              </div>
              <div>
                <div className="text-xs text-muted-foreground">{fraudCopy.labels.lastDetected}</div>
                <SelectedDetailValue value={item.last_time} />
              </div>
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">{fraudCopy.labels.details}</div>
            {detailMetrics.length > 0 ? (
              <dl className="grid gap-x-3 gap-y-2 rounded border border-border bg-muted/20 p-3 sm:grid-cols-2">
                {detailMetrics.map((metric) => (
                  <div key={metric.key}>
                    <dt className="text-xs text-muted-foreground">{metric.label}</dt>
                    <dd className="mt-0.5 text-sm text-foreground">{metric.value}</dd>
                  </div>
                ))}
              </dl>
            ) : (
              <div className="text-sm text-muted-foreground">{fraudCopy.labels.detailsEmpty}</div>
            )}
          </div>
        </div>
      )}
    </aside>
  );
}
