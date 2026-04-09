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
  ReviewReasonDialog,
  RiskBadge,
  StatusBadge,
} from "@/components/console-ui";
import { getAlertDetail, reviewAlerts } from "@/lib/console-api";
import type { AlertDetailResponse, ReviewStatus } from "@/lib/console-types";
import type { ConsoleViewerRole } from "@/lib/console-viewer";
import { formatCurrency, formatDateTime } from "@/lib/format";

type AlertDetailScreenProps = {
  caseKey: string;
  viewerRole: ConsoleViewerRole;
};

function rewardSourceLabel(source: string, estimated: boolean) {
  if (!estimated) {
    return "実績";
  }
  if (source === "fallback_default") {
    return "デフォルト単価による推定";
  }
  if (source === "mixed") {
    return "複合データによる推定";
  }
  return "推定";
}

function renderEntityList(items: Array<{ id: string; name: string }>) {
  if (items.length === 0) {
    return <EmptyState message="関連データはありません。" />;
  }
  return (
    <ul className="reasons-list">
      {items.map((item) => (
        <li key={`${item.id}-${item.name}`}>{`${item.name} (${item.id})`}</li>
      ))}
    </ul>
  );
}

function TransactionsTable({
  ariaLabel,
  rows,
}: {
  ariaLabel: string;
  rows: AlertDetailResponse["evidence_transactions"];
}) {
  if (rows.length === 0) {
    return <EmptyState message="トランザクションはありません。" />;
  }
  return (
    <div className="table-wrap">
      <table aria-label={ariaLabel}>
        <thead>
          <tr>
            <th>トランザクションID</th>
            <th>発生日時</th>
            <th>アフィリエイト</th>
            <th>プログラム</th>
            <th>報酬額</th>
            <th>ステータス</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((transaction) => (
            <tr key={transaction.transaction_id}>
              <td>{transaction.transaction_id}</td>
              <td>{transaction.occurred_at ? formatDateTime(transaction.occurred_at) : "-"}</td>
              <td>{transaction.affiliate_name}</td>
              <td>{transaction.program_name}</td>
              <td>{formatCurrency(transaction.reward_amount)}</td>
              <td>{transaction.state}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function statusActionLabel(status: ReviewStatus) {
  if (status === "confirmed_fraud") {
    return "不正として確定";
  }
  if (status === "white") {
    return "ホワイトとして確定";
  }
  return "調査中に変更";
}

export function AlertDetailScreen({ caseKey, viewerRole }: AlertDetailScreenProps) {
  const [data, setData] = useState<AlertDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submittingStatus, setSubmittingStatus] = useState<ReviewStatus | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus | null>(null);
  const [reviewReason, setReviewReason] = useState("");
  const [reviewReasonError, setReviewReasonError] = useState<string | null>(null);

  const loadDetail = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getAlertDetail(caseKey);
      setData(result);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "アラート詳細の取得に失敗しました。");
    } finally {
      setLoading(false);
    }
  }, [caseKey]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  useEffect(() => {
    if (reviewStatus === null) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && submittingStatus === null) {
        setReviewStatus(null);
        setReviewReason("");
        setReviewReasonError(null);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [reviewStatus, submittingStatus]);

  function openReviewDialog(status: ReviewStatus) {
    setReviewStatus(status);
    setReviewReason("");
    setReviewReasonError(null);
    setWarning(null);
  }

  function closeReviewDialog() {
    if (submittingStatus !== null) {
      return;
    }
    setReviewStatus(null);
    setReviewReason("");
    setReviewReasonError(null);
  }

  async function submitReview() {
    if (reviewStatus === null) {
      return;
    }

    const reason = reviewReason.trim();
    if (!reason) {
      setReviewReasonError("レビュー理由を入力してください。");
      return;
    }

    setSubmittingStatus(reviewStatus);
    setError(null);
    setWarning(null);
    setReviewReasonError(null);
    try {
      const result = await reviewAlerts([caseKey], reviewStatus, reason);
      setData((current) => (current ? { ...current, status: result.status } : current));
      closeReviewDialog();
      setFeedback(`${result.updated_count}件のケースを更新しました。`);
      setWarning(result.missing_keys.length > 0 ? `見つからないケース: ${result.missing_keys.join(", ")}` : null);
      await loadDetail();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "レビューの更新に失敗しました。");
    } finally {
      setSubmittingStatus(null);
    }
  }

  return (
    <div className="screen-page">
      <PageHeader
        title="アラート詳細"
        description={data?.latest_detected_at ? formatDateTime(data.latest_detected_at) : "ケース詳細"}
      />

      {loading && !data ? <LoadingState /> : null}
      {error && !data ? <ErrorState message={error} /> : null}

      {data ? (
        <div className="detail-layout">
          <div className="detail-main">
            <section className="detail-header-grid" aria-label="アラート概要">
              <div className="detail-stat detail-stat-wide">
                <div className="detail-key">アクセス環境</div>
                <div className="detail-value">{data.environment.ipaddress ?? "IP なし"}</div>
                <div className="detail-subvalue">{data.environment.useragent ?? "UA なし"}</div>
                <div className="detail-subvalue">{data.environment.date ?? "日付なし"}</div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">リスク</div>
                <div className="detail-value">
                  <RiskBadge score={data.risk_score} level={data.risk_level} emphasized />
                </div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">想定被害額</div>
                <div className="detail-value">{formatCurrency(data.reward_amount)}</div>
                <div className="detail-subvalue">
                  {rewardSourceLabel(data.reward_amount_source, data.reward_amount_is_estimated)}
                </div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">ステータス</div>
                <div className="detail-value">
                  <StatusBadge status={data.status} />
                </div>
              </div>
            </section>

            <Panel title="検知理由" description={data.primary_reason}>
              {data.reasons.length === 0 ? (
                <EmptyState message="検知理由はありません。" />
              ) : (
                <ul className="reasons-list">
                  {data.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
            </Panel>

            <Panel title="対象アフィリエイト">{renderEntityList(data.affected_affiliates)}</Panel>

            <Panel title="対象プログラム">{renderEntityList(data.affected_programs)}</Panel>

            <Panel
              title="証拠トランザクション"
              description="同一日・同一IPアドレス・同一ユーザーエージェントに限定した主要証拠です。"
            >
              <TransactionsTable ariaLabel="証拠トランザクション" rows={data.evidence_transactions} />
            </Panel>

            <Panel title="レビュー履歴" description="このケースに対するレビュー操作の履歴です。">
              {data.review_history.length === 0 ? (
                <EmptyState message="レビュー履歴はありません。" />
              ) : (
                <div className="table-wrap">
                  <table aria-label="レビュー履歴">
                    <thead>
                      <tr>
                        <th>ステータス</th>
                        <th>理由</th>
                        <th>レビュー担当</th>
                        <th>レビュー日時</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.review_history.map((item) => (
                        <tr key={`${item.reviewed_at}-${item.request_id}-${item.status}`}>
                          <td>{item.status}</td>
                          <td>{item.reason || "-"}</td>
                          <td>{`${item.reviewed_by} (${item.reviewed_role})`}</td>
                          <td>{item.reviewed_at ? formatDateTime(item.reviewed_at) : "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>

            {data.affiliate_recent_transactions.length > 0 ? (
              <Panel
                title="アフィリエイトの直近トランザクション"
                description="対象アフィリエイトの補足情報です。主要証拠テーブルとは異なります。"
              >
                <TransactionsTable
                  ariaLabel="アフィリエイトの直近トランザクション"
                  rows={data.affiliate_recent_transactions}
                />
              </Panel>
            ) : null}
          </div>

          <div className="detail-sidebar">
            {viewerRole === "admin" ? (
              <div className="detail-action-panel">
                <p className="detail-action-title">レビュー操作</p>
                <ActionButton
                  tone="danger"
                  className="button-wide"
                  disabled={submittingStatus !== null}
                  onClick={() => openReviewDialog("confirmed_fraud")}
                >
                  不正確定
                </ActionButton>
                <ActionButton
                  className="button-wide"
                  disabled={submittingStatus !== null}
                  onClick={() => openReviewDialog("white")}
                >
                  ホワイト確定
                </ActionButton>
                <ActionButton
                  tone="warning"
                  className="button-wide"
                  disabled={submittingStatus !== null}
                  onClick={() => openReviewDialog("investigating")}
                >
                  調査中に変更
                </ActionButton>
                <ActionButton className="button-wide" onClick={() => void loadDetail()} disabled={loading}>
                  再読み込み
                </ActionButton>
              </div>
            ) : null}

            {feedback ? (
              <div className="success-message" role="status" aria-live="polite">
                {feedback}
              </div>
            ) : null}
            {warning ? <ErrorState message={warning} /> : null}
            {error ? <ErrorState message={error} /> : null}

            <div className="detail-action-panel">
              <p className="detail-action-title">ケース情報</p>
              <div className="detail-meta-block">
                <div className="detail-meta-row">
                  <span>ケースキー</span>
                  <span className="detail-meta-value">{data.case_key}</span>
                </div>
                <div className="detail-meta-row">
                  <span>検知キー</span>
                  <span className="detail-meta-value">{data.finding_key}</span>
                </div>
                <div className="detail-meta-row">
                  <span>報酬額の算出元</span>
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

      <ReviewReasonDialog
        open={reviewStatus !== null}
        title="レビュー理由"
        description="ステータスを変更する理由を入力してください。"
        confirmLabel={reviewStatus ? statusActionLabel(reviewStatus) : "レビューを適用"}
        value={reviewReason}
        error={reviewReasonError}
        busy={submittingStatus !== null}
        onChange={(value) => {
          setReviewReason(value);
          if (reviewReasonError) {
            setReviewReasonError(null);
          }
        }}
        onCancel={closeReviewDialog}
        onConfirm={() => void submitReview()}
        textareaProps={{
          autoFocus: true,
          rows: 5,
          maxLength: 500,
          placeholder: "ステータスを変更する理由を記入してください。",
        }}
      />
    </div>
  );
}
