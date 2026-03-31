/**
 * 不審一覧テーブルの列モデル。
 * レイアウト（CV主役 / クリック既定）ごとに列順のみが変わり、セル内容は列 ID で対応づける。
 */

export type SuspiciousTableColumnId =
  | "metric"
  | "ip"
  | "ua"
  | "risk"
  | "reason"
  | "action";

/** CV 一覧: 先頭列をメトリックに。クリック一覧: IP 先行の従来順 */
export type SuspiciousTableLayout = "cv_conversions" | "clicks";

export type MetricKey = "total_clicks" | "total_conversions";

export const COLUMN_ORDER: Record<SuspiciousTableLayout, readonly SuspiciousTableColumnId[]> = {
  cv_conversions: ["metric", "ip", "ua", "risk", "reason", "action"],
  clicks: ["ip", "ua", "metric", "risk", "reason", "action"],
};

export function layoutFromMetricKey(metricKey: MetricKey): SuspiciousTableLayout {
  return metricKey === "total_conversions" ? "cv_conversions" : "clicks";
}
