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
    return "Observed";
  }
  if (source === "fallback_default") {
    return "Estimated from default";
  }
  if (source === "mixed") {
    return "Mixed evidence";
  }
  return "Estimated";
}

function renderEntityList(items: Array<{ id: string; name: string }>) {
  if (items.length === 0) {
    return <EmptyState message="No related entities." />;
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
    return <EmptyState message="No transactions found." />;
  }
  return (
    <div className="table-wrap">
      <table aria-label={ariaLabel}>
        <thead>
          <tr>
            <th>Transaction ID</th>
            <th>Occurred at</th>
            <th>Affiliate</th>
            <th>Program</th>
            <th>Reward</th>
            <th>Status</th>
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
    return "Mark confirmed fraud";
  }
  if (status === "white") {
    return "Mark white";
  }
  return "Mark investigating";
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
      setError(caughtError instanceof Error ? caughtError.message : "Failed to load alert detail.");
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
      setReviewReasonError("Review reason is required.");
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
      setFeedback(`Updated ${result.updated_count} case.`);
      setWarning(result.missing_keys.length > 0 ? `Missing cases: ${result.missing_keys.join(", ")}` : null);
      await loadDetail();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Failed to update review.");
    } finally {
      setSubmittingStatus(null);
    }
  }

  return (
    <div className="screen-page">
      <PageHeader
        title="Alert detail"
        description={data?.latest_detected_at ? formatDateTime(data.latest_detected_at) : "Case detail"}
      />

      {loading && !data ? <LoadingState /> : null}
      {error && !data ? <ErrorState message={error} /> : null}

      {data ? (
        <div className="detail-layout">
          <div className="detail-main">
            <section className="detail-header-grid" aria-label="Alert overview">
              <div className="detail-stat detail-stat-wide">
                <div className="detail-key">Environment</div>
                <div className="detail-value">{data.environment.ipaddress ?? "No IP"}</div>
                <div className="detail-subvalue">{data.environment.useragent ?? "No user agent"}</div>
                <div className="detail-subvalue">{data.environment.date ?? "No date"}</div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">Risk</div>
                <div className="detail-value">
                  <RiskBadge score={data.risk_score} level={data.risk_level} emphasized />
                </div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">Estimated damage</div>
                <div className="detail-value">{formatCurrency(data.reward_amount)}</div>
                <div className="detail-subvalue">
                  {rewardSourceLabel(data.reward_amount_source, data.reward_amount_is_estimated)}
                </div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">Status</div>
                <div className="detail-value">
                  <StatusBadge status={data.status} />
                </div>
              </div>
            </section>

            <Panel title="Reasons" description={data.primary_reason}>
              {data.reasons.length === 0 ? (
                <EmptyState message="No reasons found." />
              ) : (
                <ul className="reasons-list">
                  {data.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
            </Panel>

            <Panel title="Affected affiliates">{renderEntityList(data.affected_affiliates)}</Panel>

            <Panel title="Affected programs">{renderEntityList(data.affected_programs)}</Panel>

            <Panel
              title="Evidence transactions"
              description="Primary evidence is scoped to the same date, IP address, and user agent."
            >
              <TransactionsTable ariaLabel="evidence transactions" rows={data.evidence_transactions} />
            </Panel>

            <Panel title="Review history" description="Latest review events recorded for this case.">
              {data.review_history.length === 0 ? (
                <EmptyState message="No review history found." />
              ) : (
                <div className="table-wrap">
                  <table aria-label="review history">
                    <thead>
                      <tr>
                        <th>Status</th>
                        <th>Reason</th>
                        <th>Reviewed by</th>
                        <th>Reviewed at</th>
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
                description="Secondary context for the affected affiliate. This is not the primary evidence table."
              >
                <TransactionsTable
                  ariaLabel="affiliate recent transactions"
                  rows={data.affiliate_recent_transactions}
                />
              </Panel>
            ) : null}
          </div>

          <div className="detail-sidebar">
            {viewerRole === "admin" ? (
              <div className="detail-action-panel">
                <p className="detail-action-title">Review actions</p>
                <ActionButton
                  tone="danger"
                  className="button-wide"
                  disabled={submittingStatus !== null}
                  onClick={() => openReviewDialog("confirmed_fraud")}
                >
                  Mark fraud
                </ActionButton>
                <ActionButton
                  className="button-wide"
                  disabled={submittingStatus !== null}
                  onClick={() => openReviewDialog("white")}
                >
                  Mark white
                </ActionButton>
                <ActionButton
                  tone="warning"
                  className="button-wide"
                  disabled={submittingStatus !== null}
                  onClick={() => openReviewDialog("investigating")}
                >
                  Mark investigating
                </ActionButton>
                <ActionButton className="button-wide" onClick={() => void loadDetail()} disabled={loading}>
                  Refresh detail
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
              <p className="detail-action-title">Case metadata</p>
              <div className="detail-meta-block">
                <div className="detail-meta-row">
                  <span>Case key</span>
                  <span className="detail-meta-value">{data.case_key}</span>
                </div>
                <div className="detail-meta-row">
                  <span>Finding key</span>
                  <span className="detail-meta-value">{data.finding_key}</span>
                </div>
                <div className="detail-meta-row">
                  <span>Reward source</span>
                  <span className="detail-meta-value">
                    {rewardSourceLabel(data.reward_amount_source, data.reward_amount_is_estimated)}
                  </span>
                </div>
              </div>
            </div>

            <Link className="top-link" href="/alerts">
              Back to alerts
            </Link>
          </div>
        </div>
      ) : null}

      <ReviewReasonDialog
        open={reviewStatus !== null}
        title="Review reason"
        description="Add the reason for this review change before applying the new status."
        confirmLabel={reviewStatus ? statusActionLabel(reviewStatus) : "Apply review"}
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
          placeholder: "Describe why this case status is changing.",
        }}
      />
    </div>
  );
}
