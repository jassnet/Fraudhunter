"use client";

import { useEffect, useState } from "react";

import { LineChart } from "@/components/line-chart";
import {
  ActionButton,
  EmptyState,
  ErrorState,
  LoadingState,
  MetricStrip,
  PageHeader,
  Panel,
} from "@/components/console-ui";
import { getDashboard } from "@/lib/console-api";
import type { DashboardResponse } from "@/lib/console-types";
import { formatCurrency, formatDateLabel, formatPercent } from "@/lib/format";

function resolveKpiTone(key: string, value: number): "danger" | "warning" | "neutral" {
  if (key === "fraud_rate") {
    if (value > 10) return "danger";
    if (value > 5) return "warning";
  }
  if (key === "unhandled_alerts") {
    if (value > 20) return "danger";
  }
  return "neutral";
}

const KPI_DEFINITIONS = [
  {
    key: "fraud_rate",
    label: "全体フラウド率",
    format: (value: number) => formatPercent(value),
  },
  {
    key: "unhandled_alerts",
    label: "未対応アラート件数",
    format: (value: number) => `${value}件`,
  },
  {
    key: "estimated_damage",
    label: "被害推定額",
    format: (value: number) => formatCurrency(value),
  },
] as const;

export function DashboardScreen() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDashboard() {
    setLoading(true);
    setError(null);
    try {
      const result = await getDashboard();
      setData(result);
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "ダッシュボードの取得に失敗しました。";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  const dateLabel = data ? `${formatDateLabel(data.date)} 時点` : "";

  return (
    <div className="dashboard-page">
      <PageHeader
        title="ダッシュボード"
        description={dateLabel}
        actions={
          <ActionButton onClick={() => void loadDashboard()} disabled={loading}>
            再読み込み
          </ActionButton>
        }
      />

      {loading && !data ? <LoadingState /> : null}
      {error && !data ? <ErrorState message={error} /> : null}

      {data ? (
        <>
          <MetricStrip
            items={KPI_DEFINITIONS.map((definition) => {
              const metric = data.kpis[definition.key];
              return {
                label: definition.label,
                value: definition.format(metric.value),
                caption: `${formatDateLabel(data.date)} 集計`,
                tone: resolveKpiTone(definition.key, metric.value),
              };
            })}
          />

          <div className="dashboard-body">
            <Panel title="検知件数推移">
              <LineChart data={data.trend} />
            </Panel>

            <Panel title="フラウド率ランキング" className="panel--scroll">
              {data.ranking.length === 0 ? (
                <EmptyState message="ランキング対象のアフィリエイターはありません。" />
              ) : (
                <div className="table-wrap">
                  <table aria-label="フラウド率ランキング">
                    <thead>
                      <tr>
                        <th>アフィリエイター</th>
                        <th>フラウド率</th>
                        <th>件数</th>
                        <th>被害額</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.ranking.map((affiliate) => (
                        <tr key={affiliate.affiliate_id}>
                          <td>
                            <div className="table-primary">{affiliate.affiliate_name}</div>
                            <div className="table-secondary">{affiliate.affiliate_id}</div>
                          </td>
                          <td>{formatPercent(affiliate.fraud_rate)}</td>
                          <td>{affiliate.alert_count}</td>
                          <td>{formatCurrency(affiliate.estimated_damage)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>
          </div>
        </>
      ) : null}
    </div>
  );
}
