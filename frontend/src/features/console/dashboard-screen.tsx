"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useConsoleDisplayMode } from "@/components/console-display-mode";
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
import { getDashboard, getJobStatus, refreshLatestData, syncMasterData } from "@/lib/console-api";
import type { DashboardResponse, JobStatusResponse } from "@/lib/console-types";
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
  searchParams?: Record<string, string | string[] | undefined>;
};

function firstSearchParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

function resolveTargetDate(searchParams?: Record<string, string | string[] | undefined>) {
  const value = firstSearchParam(searchParams?.target_date);
  return value || "";
}

function isActiveJobStatus(status: string | undefined) {
  return status === "queued" || status === "running";
}

function kpiCaption(key: string, data: DashboardResponse) {
  if (key === "fraud_rate") {
    return `${formatDateLabel(data.target_date)} の一日の集計`;
  }
  return "全期間の未対応件数";
}

export function DashboardScreen({ searchParams }: DashboardScreenProps) {
  const routeTargetDate = useMemo(() => resolveTargetDate(searchParams), [searchParams]);
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [syncingMasters, setSyncingMasters] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const { replace } = useRouter();
  const pathname = usePathname();
  const { showAdvanced } = useConsoleDisplayMode();

  const loadDashboard = useCallback(async (targetDate = routeTargetDate) => {
    setLoading(true);
    setError(null);
    try {
      const result = await getDashboard(targetDate || undefined);
      setData(result);
      setJobStatus(result.job_status_summary);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "ダッシュボードの取得に失敗しました。");
    } finally {
      setLoading(false);
    }
  }, [routeTargetDate]);

  useEffect(() => {
    void loadDashboard(routeTargetDate);
  }, [loadDashboard, routeTargetDate]);

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
          await loadDashboard(routeTargetDate);
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
  }, [activeJobId, loadDashboard, routeTargetDate]);

  function replaceRoute(targetDate: string) {
    const query = new URLSearchParams();
    if (targetDate) {
      query.set("target_date", targetDate);
    }
    const suffix = query.toString() ? `?${query.toString()}` : "";
    replace(`${pathname}${suffix}`, { scroll: false });
  }

  async function handleRefresh() {
    setRefreshing(true);
    setFeedback(null);
    setActionError(null);
    try {
      const result = await refreshLatestData();
      const jobId = result.details?.job_id ?? null;
      setActiveJobId(jobId);
      setFeedback(jobId ? "最新データの反映を開始しました。完了までしばらくお待ちください。" : result.message);
      if (jobId) {
        setJobStatus(await getJobStatus(jobId));
      } else {
        await loadDashboard(routeTargetDate);
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
      setFeedback(jobId ? "基本データの同期を開始しました。完了までしばらくお待ちください。" : result.message);
      if (jobId) {
        setJobStatus(await getJobStatus(jobId));
      } else {
        await loadDashboard(routeTargetDate);
      }
    } catch (caughtError) {
      setActionError(caughtError instanceof Error ? caughtError.message : "基本データの同期開始に失敗しました。");
    } finally {
      setSyncingMasters(false);
    }
  }

  const freshness = useMemo(
    () => ({
      ingest: data?.quality?.last_successful_ingest_at ?? null,
      findings: data?.quality?.findings?.findings_last_computed_at ?? null,
      masterSync: data?.quality?.master_sync?.last_synced_at ?? null,
      stale: data?.quality?.findings?.stale ?? false,
      staleReasons: data?.quality?.findings?.stale_reasons ?? [],
    }),
    [data],
  );

  const queue = jobStatus?.queue ?? data?.job_status_summary?.queue ?? null;

  return (
    <div className="dashboard-page">
      <PageHeader
        title="ダッシュボード"
        description={data ? `${formatDateLabel(data.target_date)} の集計（未対応件数は全期間の合計）` : ""}
        actions={
          <>
            {data?.available_dates?.length ? (
              <label className="form-field form-field--compact dashboard-date-filter">
                <span>日付</span>
                <select value={routeTargetDate} onChange={(event) => replaceRoute(event.target.value)}>
                  <option value="">最新</option>
                  {data.available_dates.map((value) => (
                    <option key={value} value={value}>
                      {formatDateLabel(value)}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <Link className="button button-default" href="/alerts">
              アラート一覧
            </Link>
            {showAdvanced ? (
              <ActionButton
                tone="warning"
                onClick={() => void handleRefresh()}
                disabled={loading || refreshing || syncingMasters}
              >
                データ再取得
              </ActionButton>
            ) : null}
            {showAdvanced ? (
              <ActionButton
                onClick={() => void handleMasterSync()}
                disabled={loading || refreshing || syncingMasters}
              >
                基本データ同期
              </ActionButton>
            ) : null}
            <ActionButton onClick={() => void loadDashboard(routeTargetDate)} disabled={loading || refreshing || syncingMasters}>
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
            <ErrorState message={`検知結果が最新ではありません（${freshness.staleReasons.join("、") || "理由不明"}）。再計算をおすすめします。`} />
          ) : null}

          <MetricStrip
            items={KPI_DEFINITIONS.map((definition) => {
              const metric = data.kpis[definition.key];
              return {
                label: definition.label,
                value: definition.format(metric.value),
                caption: kpiCaption(definition.key, data),
                tone: resolveKpiTone(definition.key, metric.value),
              };
            })}
          />

          <div className="dashboard-body">
            <Panel title="検知件数の推移" description="不正率は選択日の一日分、未対応件数は全期間の合計を反映します。">
              <LineChart data={data.trend} />
            </Panel>

            <div className="dashboard-sidebar">
              <Panel title="データの更新状況">
                <div className="detail-meta-block">
                  <div className="detail-meta-row">
                    <span>最新データの取得日時</span>
                    <span className="detail-meta-value">{freshness.ingest ? formatDateTime(freshness.ingest) : "-"}</span>
                  </div>
                  <div className="detail-meta-row">
                    <span>検知結果の最終更新</span>
                    <span className="detail-meta-value">{freshness.findings ? formatDateTime(freshness.findings) : "-"}</span>
                  </div>
                  <div className="detail-meta-row">
                    <span>基本データの最終同期</span>
                    <span className="detail-meta-value">{freshness.masterSync ? formatDateTime(freshness.masterSync) : "-"}</span>
                  </div>
                  <div className="detail-meta-row">
                    <span>処理の状況</span>
                    <span className="detail-meta-value">{showAdvanced && queue
                      ? `待機中 ${queue.queued ?? 0}件 / 再試行待ち ${queue.retry_scheduled ?? 0}件 / 実行中 ${queue.running ?? 0}件 / 失敗 ${queue.failed ?? 0}件`
                      : "通常表示では非表示"}</span>
                  </div>
                  {showAdvanced ? (
                    <div className="detail-meta-row">
                      <span>直近の処理</span>
                      <span className="detail-meta-value">
                        {jobStatus?.job_id ? `${jobStatus.job_id}（${jobStatus.status}）` : "なし"}
                      </span>
                    </div>
                  ) : null}
                  <div className="detail-meta-row">
                    <span>一番古い未対応</span>
                    <span className="detail-meta-value">
                      {data.operations.oldest_unhandled_days !== null ? `${data.operations.oldest_unhandled_days}日前` : "-"}
                    </span>
                  </div>
                  <div className="detail-meta-row">
                    <span>3日以上放置中</span>
                    <span className="detail-meta-value">{data.operations.stale_unhandled_count}件</span>
                  </div>
                </div>
                {showAdvanced ? (
                  <div className="dashboard-inline-section">
                    <div className="dashboard-inline-title">次の自動実行予定</div>
                    {data.operations.schedules.length ? (
                      <ul className="dashboard-inline-list">
                        {data.operations.schedules.map((item) => (
                          <li key={item.key}>
                            <span>{item.label}</span>
                            <span>{item.next_run_at ? formatDateTime(item.next_run_at) : "-"}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <EmptyState message="自動実行の予定はありません。" />
                    )}
                  </div>
                ) : null}
                {showAdvanced ? (
                  <div className="dashboard-inline-section">
                    <div className="dashboard-inline-title">直近の失敗処理</div>
                    {data.operations.failed_jobs.length ? (
                      <ul className="dashboard-inline-list dashboard-inline-list--stack">
                        {data.operations.failed_jobs.map((item) => (
                          <li key={item.job_id}>
                            <strong>{item.job_type}</strong>
                            <span>{item.finished_at ? formatDateTime(item.finished_at) : "-"}</span>
                            <span>{item.error_message || item.message || "エラー内容の記録なし"}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <EmptyState message="失敗した処理はありません。" />
                    )}
                  </div>
                ) : null}
              </Panel>

              <Panel title="判定結果の内訳" description="全期間のケースに対する最新の判定状況です。">
                <div className="detail-meta-block">
                  <div className="detail-meta-row">
                    <span>不正と確定</span>
                    <span className="detail-meta-value">{data.review_outcomes.confirmed_fraud}件</span>
                  </div>
                  <div className="detail-meta-row">
                    <span>正常（ホワイト）と確定</span>
                    <span className="detail-meta-value">{data.review_outcomes.white}件</span>
                  </div>
                  <div className="detail-meta-row">
                    <span>調査中</span>
                    <span className="detail-meta-value">{data.review_outcomes.investigating}件</span>
                  </div>
                  <div className="detail-meta-row">
                    <span>不正確定の割合</span>
                    <span className="detail-meta-value">
                      {data.review_outcomes.confirmed_ratio !== null ? `${data.review_outcomes.confirmed_ratio}%` : "-"}
                    </span>
                  </div>
                </div>
              </Panel>

            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
