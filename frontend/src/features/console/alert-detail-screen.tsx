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
      const message = caughtError instanceof Error ? caughtError.message : "アラート詳細の取得に失敗しました。";
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
      setFeedback("ステータスを更新しました。");
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "アラート更新に失敗しました。";
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
      <PageHeader title="アラート詳細" description="" />

      {loading && !data ? <LoadingState /> : null}
      {error && !data ? <ErrorState message={error} /> : null}

      {data ? (
        <div className="detail-layout">
          {/* 左カラム: 情報エリア */}
          <div className="detail-main">
            {/* 概要統計グリッド */}
            <section className="detail-header-grid" aria-label="アラート概要">
              <div className="detail-stat detail-stat-wide">
                <div className="detail-key">アフィリエイトID / 名称</div>
                <div className="detail-value">{data.affiliate_id}</div>
                <div className="detail-subvalue">{data.affiliate_name}</div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">リスクスコア</div>
                <div className="detail-value">
                  <RiskBadge score={data.risk_score} level={data.risk_level} emphasized />
                </div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">報酬額</div>
                <div className="detail-value">{formatCurrency(data.reward_amount)}</div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">検知日時</div>
                <div className="detail-value" style={{ fontSize: "15px" }}>{formatDateTime(data.detected_at)}</div>
              </div>
            </section>

            {/* 検知根拠 */}
            <Panel title="検知根拠" description={`${data.outcome_type} / ${data.program_name ?? "案件未設定"}`}>
              {data.reasons.length === 0 ? (
                <EmptyState message="判定根拠はまだ記録されていません。" />
              ) : (
                <ul className="reasons-list">
                  {data.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
            </Panel>

            {/* 関連トランザクション */}
            <Panel title="関連トランザクション" description="同一アフィリエイターの直近成果">
              {data.transactions.length === 0 ? (
                <EmptyState message="関連するトランザクションはありません。" />
              ) : (
                <div className="table-wrap">
                  <table aria-label="関連トランザクション">
                    <thead>
                      <tr>
                        <th>成果ID</th>
                        <th>発生日時</th>
                        <th>成果種別</th>
                        <th>報酬額</th>
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

          {/* 右カラム: アクションエリア（sticky） */}
          <div className="detail-sidebar">
            {/* 現在のステータス */}
            <div className="detail-action-panel">
              <p className="detail-action-title">現在のステータス</p>
              <div className="detail-status-block">
                <StatusBadge status={data.status} />
              </div>
            </div>

            {/* アクションボタン */}
            <div className="detail-action-panel">
              <p className="detail-action-title">対処アクション</p>
              <ActionButton
                tone="danger"
                className="button-wide"
                disabled={submittingStatus !== null}
                onClick={() => void handleReview("confirmed_fraud")}
              >
                確定不正にする
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
              <ActionButton
                className="button-wide"
                onClick={() => void loadDetail()}
                disabled={loading}
              >
                再取得
              </ActionButton>
              {feedback ? <div className="success-message">{feedback}</div> : null}
              {error ? <ErrorState message={error} /> : null}
            </div>

            {/* メタデータ */}
            <div className="detail-action-panel">
              <p className="detail-action-title">詳細情報</p>
              <div className="detail-meta-block">
                <div className="detail-meta-row">
                  <span>成果種別</span>
                  <span className="detail-meta-value">{data.outcome_type}</span>
                </div>
                <div className="detail-meta-row">
                  <span>案件名</span>
                  <span className="detail-meta-value">{data.program_name ?? "未設定"}</span>
                </div>
              </div>
            </div>

            {/* 戻るリンク */}
            <Link className="top-link" href="/alerts">
              ← アラート一覧に戻る
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
