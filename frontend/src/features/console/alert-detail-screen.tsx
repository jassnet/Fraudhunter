"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  ActionButton,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  Panel,
  RiskBadge,
  StatusBadge,
} from "@/components/console-ui";
import { getAlertDetail, reviewAlerts } from "@/lib/console-api";
import type { AlertDetailResponse, ReviewStatus } from "@/lib/console-types";
import { formatCurrency, formatDateTime } from "@/lib/format";

type AlertDetailScreenProps = {
  findingKey: string;
};

function rewardSourceLabel(source: string, estimated: boolean) {
  if (!estimated) {
    return "実測値";
  }
  if (source === "fallback_default") {
    return "既定単価の推定";
  }
  if (source === "mixed") {
    return "一部推定";
  }
  return "推定値";
}

export function AlertDetailScreen({ findingKey }: AlertDetailScreenProps) {
  const [data, setData] = useState<AlertDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submittingStatus, setSubmittingStatus] = useState<ReviewStatus | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const loadDetail = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getAlertDetail(findingKey);
      setData(result);
    } catch (caughtError) {
      const message =
        caughtError instanceof Error ? caughtError.message : "アラート詳細の取得に失敗しました。";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [findingKey]);

  async function handleReview(status: ReviewStatus) {
    setSubmittingStatus(status);
    setError(null);
    try {
      const result = await reviewAlerts([findingKey], status);
      setData((current) => (current ? { ...current, status: result.status } : current));
      setFeedback("レビュー状態を更新しました。");
    } catch (caughtError) {
      const message =
        caughtError instanceof Error ? caughtError.message : "アラート更新に失敗しました。";
      setError(message);
    } finally {
      setSubmittingStatus(null);
    }
  }

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  return (
    <div className="screen-page">
      <PageHeader
        title="アラート詳細"
        description="根拠、関連トランザクション、レビュー状態を確認します。"
      />

      {loading && !data ? <LoadingState /> : null}
      {error && !data ? <ErrorState message={error} /> : null}

      {data ? (
        <div className="detail-layout">
          <div className="detail-main">
            <section className="detail-header-grid" aria-label="アラート概要">
              <div className="detail-stat detail-stat-wide">
                <div className="detail-key">アフィリエイター名</div>
                <div className="detail-value">{data.affiliate_name}</div>
                <div className="detail-subvalue">{`ID: ${data.affiliate_id}`}</div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">リスク</div>
                <div className="detail-value">
                  <RiskBadge score={data.risk_score} level={data.risk_level} emphasized />
                </div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">想定報酬</div>
                <div className="detail-value">{formatCurrency(data.reward_amount)}</div>
                <div className="detail-subvalue">
                  {rewardSourceLabel(data.reward_amount_source, data.reward_amount_is_estimated)}
                </div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">検知日時</div>
                <div className="detail-value detail-value-small">{formatDateTime(data.detected_at)}</div>
              </div>
            </section>

            <Panel
              title="検知理由"
              description={`広告名: ${data.program_name ?? "未設定"} / 成果種別: ${data.outcome_type}`}
            >
              {data.reasons.length === 0 ? (
                <EmptyState message="検知理由はまだ登録されていません。" />
              ) : (
                <ul className="reasons-list">
                  {data.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
            </Panel>

            <Panel title="関連トランザクション" description="同一アフィリエイトの直近トランザクションを表示します。">
              {data.transactions.length === 0 ? (
                <EmptyState message="関連トランザクションはありません。" />
              ) : (
                <div className="table-wrap">
                  <table aria-label="関連トランザクション">
                    <thead>
                      <tr>
                        <th>取引ID</th>
                        <th>発生日時</th>
                        <th>成果</th>
                        <th>報酬</th>
                        <th>状態</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.transactions.map((transaction) => (
                        <tr key={transaction.transaction_id}>
                          <td>{transaction.transaction_id}</td>
                          <td>{formatDateTime(transaction.occurred_at)}</td>
                          <td>{transaction.outcome_type}</td>
                          <td>{formatCurrency(transaction.reward_amount)}</td>
                          <td>{transaction.state}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>
          </div>

          <div className="detail-sidebar">
            <div className="detail-action-panel">
              <p className="detail-action-title">レビュー状態</p>
              <div className="detail-status-block">
                <StatusBadge status={data.status} />
              </div>
            </div>

            <div className="detail-action-panel">
              <p className="detail-action-title">レビュー操作</p>
              <ActionButton
                tone="danger"
                className="button-wide"
                disabled={submittingStatus !== null}
                onClick={() => void handleReview("confirmed_fraud")}
              >
                不正にする
              </ActionButton>
              <ActionButton
                className="button-wide"
                disabled={submittingStatus !== null}
                onClick={() => void handleReview("white")}
              >
                ホワイトにする
              </ActionButton>
              <ActionButton
                tone="warning"
                className="button-wide"
                disabled={submittingStatus !== null}
                onClick={() => void handleReview("investigating")}
              >
                調査中にする
              </ActionButton>
              <ActionButton className="button-wide" onClick={() => void loadDetail()} disabled={loading}>
                再読み込み
              </ActionButton>
              {feedback ? <div className="success-message">{feedback}</div> : null}
              {error ? <ErrorState message={error} /> : null}
            </div>

            <div className="detail-action-panel">
              <p className="detail-action-title">補足情報</p>
              <div className="detail-meta-block">
                <div className="detail-meta-row">
                  <span>成果</span>
                  <span className="detail-meta-value">{data.outcome_type}</span>
                </div>
                <div className="detail-meta-row">
                  <span>広告名</span>
                  <span className="detail-meta-value">{data.program_name ?? "未設定"}</span>
                </div>
                <div className="detail-meta-row">
                  <span>報酬ソース</span>
                  <span className="detail-meta-value">
                    {rewardSourceLabel(data.reward_amount_source, data.reward_amount_is_estimated)}
                  </span>
                </div>
              </div>
            </div>

            <Link className="top-link" href="/alerts">
              アラート一覧に戻る
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
