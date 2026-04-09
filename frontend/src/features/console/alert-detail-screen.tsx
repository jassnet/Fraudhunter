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
import type { ConsoleViewerRole } from "@/lib/console-viewer";
import { formatCurrency, formatDateTime } from "@/lib/format";

type AlertDetailScreenProps = {
  caseKey: string;
  viewerRole: ConsoleViewerRole;
};

function rewardSourceLabel(source: string, estimated: boolean) {
  if (!estimated) {
    return "実測";
  }
  if (source === "fallback_default") {
    return "既定単価から推定";
  }
  if (source === "mixed") {
    return "一部推定あり";
  }
  return "推定";
}

function promptReviewReason() {
  const reason = globalThis.prompt?.("レビュー理由を入力してください。");
  return reason?.trim() ?? "";
}

function renderEntityList(items: Array<{ id: string; name: string }>) {
  if (items.length === 0) {
    return <EmptyState message="対象はありません。" />;
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
    return <EmptyState message="対象の取引はありません。" />;
  }
  return (
    <div className="table-wrap">
      <table aria-label={ariaLabel}>
        <thead>
          <tr>
            <th>取引ID</th>
            <th>発生日時</th>
            <th>affiliate</th>
            <th>案件</th>
            <th>金額</th>
            <th>状態</th>
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

export function AlertDetailScreen({ caseKey, viewerRole }: AlertDetailScreenProps) {
  const [data, setData] = useState<AlertDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submittingStatus, setSubmittingStatus] = useState<ReviewStatus | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);

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

  async function handleReview(status: ReviewStatus) {
    const reason = promptReviewReason();
    if (!reason) {
      setWarning("レビュー理由を入力しない限り更新できません。");
      return;
    }

    setSubmittingStatus(status);
    setError(null);
    setWarning(null);
    try {
      const result = await reviewAlerts([caseKey], status, reason);
      setData((current) => (current ? { ...current, status: result.status } : current));
      setFeedback(`${result.updated_count}件のケースを更新しました。`);
      setWarning(result.missing_keys.length > 0 ? `見つからないケース: ${result.missing_keys.join(", ")}` : null);
      await loadDetail();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "レビュー更新に失敗しました。");
    } finally {
      setSubmittingStatus(null);
    }
  }

  return (
    <div className="screen-page">
      <PageHeader
        title="アラート詳細"
        description={data?.latest_detected_at ? formatDateTime(data.latest_detected_at) : "ケース単位の詳細"}
      />

      {loading && !data ? <LoadingState /> : null}
      {error && !data ? <ErrorState message={error} /> : null}

      {data ? (
        <div className="detail-layout">
          <div className="detail-main">
            <section className="detail-header-grid" aria-label="アラート概要">
              <div className="detail-stat detail-stat-wide">
                <div className="detail-key">環境</div>
                <div className="detail-value">{data.environment.ipaddress ?? "IPなし"}</div>
                <div className="detail-subvalue">{data.environment.useragent ?? "UAなし"}</div>
                <div className="detail-subvalue">{data.environment.date ?? "日付なし"}</div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">リスク</div>
                <div className="detail-value">
                  <RiskBadge score={data.risk_score} level={data.risk_level} emphasized />
                </div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">想定被害</div>
                <div className="detail-value">{formatCurrency(data.reward_amount)}</div>
                <div className="detail-subvalue">
                  {rewardSourceLabel(data.reward_amount_source, data.reward_amount_is_estimated)}
                </div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">状態</div>
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

            <Panel title="影響affiliate">
              {renderEntityList(data.affected_affiliates)}
            </Panel>

            <Panel title="影響program">
              {renderEntityList(data.affected_programs)}
            </Panel>

            <Panel
              title="Evidence transactions"
              description="date + IP + useragent が一致する取引だけを表示します。"
            >
              <TransactionsTable ariaLabel="evidence transactions" rows={data.evidence_transactions} />
            </Panel>

            <Panel
              title="Review history"
              description="誰が、いつ、どの理由で更新したかを記録します。"
            >
              {data.review_history.length === 0 ? (
                <EmptyState message="レビュー履歴はありません。" />
              ) : (
                <div className="table-wrap">
                  <table aria-label="review history">
                    <thead>
                      <tr>
                        <th>状態</th>
                        <th>理由</th>
                        <th>レビュー担当</th>
                        <th>時刻</th>
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
                title="Affiliate recent transactions"
                description="同一affiliateの直近取引です。evidence とは別パネルで扱います。"
              >
                <TransactionsTable ariaLabel="affiliate recent transactions" rows={data.affiliate_recent_transactions} />
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
              <p className="detail-action-title">補足情報</p>
              <div className="detail-meta-block">
                <div className="detail-meta-row">
                  <span>case key</span>
                  <span className="detail-meta-value">{data.case_key}</span>
                </div>
                <div className="detail-meta-row">
                  <span>finding key</span>
                  <span className="detail-meta-value">{data.finding_key}</span>
                </div>
                <div className="detail-meta-row">
                  <span>金額根拠</span>
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
