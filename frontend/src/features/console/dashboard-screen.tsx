"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { LineChart } from "@/components/line-chart";
import {
  ActionButton,
  ErrorState,
  LoadingState,
  MetricStrip,
  PageHeader,
  Panel,
} from "@/components/console-ui";
import { getDashboard, getJobStatus, refreshLatestData, syncMasterData } from "@/lib/console-api";
import type { DashboardResponse, JobStatusResponse } from "@/lib/console-types";
import type { ConsoleViewerRole } from "@/lib/console-viewer";
import { formatCurrency, formatDateLabel, formatDateTime, formatPercent } from "@/lib/format";

function resolveKpiTone(key: string, value: number): "danger" | "warning" | "neutral" {
  if (key === "fraud_rate") {
    if (value > 10) return "danger";
    if (value > 5) return "warning";
  }
  if (key === "unhandled_alerts" && value > 20) {
    return "danger";
  }
  return "neutral";
}

const KPI_DEFINITIONS = [
  { key: "fraud_rate", label: "不正率", format: (value: number) => formatPercent(value) },
  { key: "unhandled_alerts", label: "未対応アラート件数", format: (value: number) => `${value}件` },
  { key: "estimated_damage", label: "想定被害額", format: (value: number) => formatCurrency(value) },
] as const;

type DashboardScreenProps = {
  viewerRole: ConsoleViewerRole;
};

function isActiveJobStatus(status: string | undefined) {
  return status === "queued" || status === "running";
}

export function DashboardScreen({ viewerRole }: DashboardScreenProps) {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [syncingMasters, setSyncingMasters] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  async function loadDashboard() {
    setLoading(true);
    setError(null);
    try {
      const result = await getDashboard();
      setData(result);
      setJobStatus(result.job_status_summary);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "ダッシュボードの取得に失敗しました。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  useEffect(() => {
    if (!activeJobId) {
      return;
    }
    let cancelled = false;
    const timer = window.setInterval(async () => {
      try {
        const status = await getJobStatus(activeJobId);
        if (cancelled) {
          return;
        }
        setJobStatus(status);
        if (!isActiveJobStatus(status.status)) {
          setActiveJobId(null);
          await loadDashboard();
        }
      } catch {
        if (!cancelled) {
          setActiveJobId(null);
        }
      }
    }, 3000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [activeJobId]);

  async function handleRefresh() {
    setRefreshing(true);
    setFeedback(null);
    setActionError(null);
    try {
      const result = await refreshLatestData();
      const jobId = result.details?.job_id ?? null;
      setActiveJobId(jobId);
      setFeedback(jobId ? `最新データの反映を開始しました。job: ${jobId}` : result.message);
      if (jobId) {
        setJobStatus(await getJobStatus(jobId));
      } else {
        await loadDashboard();
      }
    } catch (caughtError) {
      setActionError(caughtError instanceof Error ? caughtError.message : "最新データの更新に失敗しました。");
    } finally {
      setRefreshing(false);
    }
  }

  async function handleMasterSync() {
    setSyncingMasters(true);
    setFeedback(null);
    setActionError(null);
    try {
      const result = await syncMasterData();
      const jobId = result.details?.job_id ?? null;
      setActiveJobId(jobId);
      setFeedback(jobId ? `マスター同期を開始しました。job: ${jobId}` : result.message);
      if (jobId) {
        setJobStatus(await getJobStatus(jobId));
      } else {
        await loadDashboard();
      }
    } catch (caughtError) {
      setActionError(caughtError instanceof Error ? caughtError.message : "マスター同期の開始に失敗しました。");
    } finally {
      setSyncingMasters(false);
    }
  }

  const freshness = useMemo(() => ({
    ingest: data?.quality?.last_successful_ingest_at ?? null,
    findings: data?.quality?.findings?.findings_last_computed_at ?? null,
    masterSync: data?.quality?.master_sync?.last_synced_at ?? null,
    stale: data?.quality?.findings?.stale ?? false,
    staleReasons: data?.quality?.findings?.stale_reasons ?? [],
  }), [data]);

  const queue = jobStatus?.queue ?? data?.job_status_summary?.queue ?? null;

  return (
    <div className="dashboard-page">
      <PageHeader
        title="ダッシュボード"
        description={data ? `${formatDateLabel(data.date)} 時点` : ""}
        actions={
          <>
            <Link className="button button-default" href="/alerts">
              アラート一覧
            </Link>
            {viewerRole === "admin" ? (
              <>
                <ActionButton
                  tone="warning"
                  onClick={() => void handleRefresh()}
                  disabled={loading || refreshing || syncingMasters}
                >
                  更新
                </ActionButton>
                <ActionButton
                  onClick={() => void handleMasterSync()}
                  disabled={loading || refreshing || syncingMasters}
                >
                  マスター同期
                </ActionButton>
              </>
            ) : null}
            <ActionButton onClick={() => void loadDashboard()} disabled={loading || refreshing || syncingMasters}>
              再読み込み
            </ActionButton>
          </>
        }
      />

      {feedback ? (
        <div className="success-message" role="status" aria-live="polite">
          {feedback}
        </div>
      ) : null}
      {actionError ? <ErrorState message={actionError} /> : null}
      {loading && !data ? <LoadingState /> : null}
      {error && !data ? <ErrorState message={error} /> : null}

      {data ? (
        <>
          {freshness.stale ? (
            <ErrorState message={`検知結果が最新ではありません: ${freshness.staleReasons.join(", ") || "理由不明"}`} />
          ) : null}

          <MetricStrip
            items={KPI_DEFINITIONS.map((definition) => {
              const metric = data.kpis[definition.key];
              return {
                label: definition.label,
                value: definition.format(metric.value),
                caption: `${formatDateLabel(data.date)} 時点`,
                tone: resolveKpiTone(definition.key, metric.value),
              };
            })}
          />

          <div className="dashboard-body">
            <Panel title="検知件数推移">
              <LineChart data={data.trend} />
            </Panel>

            <Panel title="データ鮮度 / キュー">
              <div className="detail-meta-block">
                <div className="detail-meta-row">
                  <span>最終データ取込</span>
                  <span className="detail-meta-value">{freshness.ingest ? formatDateTime(freshness.ingest) : "-"}</span>
                </div>
                <div className="detail-meta-row">
                  <span>最終検知結果算出</span>
                  <span className="detail-meta-value">{freshness.findings ? formatDateTime(freshness.findings) : "-"}</span>
                </div>
                <div className="detail-meta-row">
                  <span>最終マスター同期</span>
                  <span className="detail-meta-value">{freshness.masterSync ? formatDateTime(freshness.masterSync) : "-"}</span>
                </div>
                <div className="detail-meta-row">
                  <span>キュー</span>
                  <span className="detail-meta-value">
                    {queue ? `待機 ${queue.queued ?? 0} / 実行中 ${queue.running ?? 0} / 失敗 ${queue.failed ?? 0}` : "-"}
                  </span>
                </div>
                <div className="detail-meta-row">
                  <span>最新ジョブ</span>
                  <span className="detail-meta-value">
                    {jobStatus?.job_id ? `${jobStatus.job_id} (${jobStatus.status})` : "なし"}
                  </span>
                </div>
              </div>
            </Panel>
          </div>
        </>
      ) : null}
    </div>
  );
}
