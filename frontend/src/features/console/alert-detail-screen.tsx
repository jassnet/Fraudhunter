"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useConsoleDisplayMode } from "@/components/console-display-mode";
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
import { assignAlerts, getAlertDetail, reviewAlerts, updateFollowUpTask } from "@/lib/console-api";
import type { AlertDetailResponse, ReviewStatus } from "@/lib/console-types";
import { formatCurrency, formatDateTime } from "@/lib/format";
import {
  reviewReasonPresets,
  reviewStatusActionLabel,
  reviewStatusConfirmTone,
  useReviewReasonDialog,
} from "./review-reason-dialog";

type AlertDetailScreenProps = {
  caseKey: string;
  viewerUserId: string;
  returnTo?: string;
};

function sanitizeReturnTo(returnTo?: string) {
  if (!returnTo) {
    return "/alerts";
  }
  if (!returnTo.startsWith("/alerts")) {
    return "/alerts";
  }
  if (returnTo.startsWith("//")) {
    return "/alerts";
  }
  return returnTo;
}

function buildAlertDetailHref(caseKey: string, returnTo: string) {
  const searchParams = new URLSearchParams();
  searchParams.set("returnTo", returnTo);
  return `/alerts/${encodeURIComponent(caseKey)}?${searchParams.toString()}`;
}

function rewardSourceLabel(source: string, estimated: boolean) {
  if (!estimated) {
    return "実績の金額";
  }
  if (source === "fallback_default") {
    return "標準単価による推定金額";
  }
  if (source === "mixed") {
    return "複数データから算出した推定金額";
  }
  return "推定の金額";
}

function renderEntityList(
  items: Array<{ id: string; name: string }>,
  { linkToAlerts = false, showAdvanced = false }: { linkToAlerts?: boolean; showAdvanced?: boolean } = {},
) {
  if (items.length === 0) {
    return <EmptyState message="関連する情報はありません。" />;
  }
  return (
    <ul className="detail-entity-list">
      {items.map((item) => (
        <li key={`${item.id}-${item.name}`} className="detail-entity-item">
          {linkToAlerts ? (
            <Link className="detail-entity-name detail-entity-link" href={`/alerts?status=all&sort=risk_desc&page=1&page_size=50&search=${encodeURIComponent(item.name)}`}>
              {item.name}
            </Link>
          ) : (
            <span className="detail-entity-name">{item.name}</span>
          )}
          {showAdvanced ? <span className="detail-entity-id">{item.id}</span> : null}
        </li>
      ))}
    </ul>
  );
}

function TransactionsTable({
  ariaLabel,
  rows,
  showAdvanced = false,
}: {
  ariaLabel: string;
  rows: AlertDetailResponse["evidence_transactions"];
  showAdvanced?: boolean;
}) {
  const [visibleCount, setVisibleCount] = useState(20);

  if (rows.length === 0) {
    return <EmptyState message="成果データはありません。" />;
  }
  const visibleRows = rows.slice(0, visibleCount);
  return (
    <>
      <div className="table-wrap detail-table-wrap">
        <table aria-label={ariaLabel} className="detail-data-table">
          <thead>
            <tr>
              {showAdvanced ? <th>成果の識別番号</th> : null}
              <th>発生日時</th>
              <th>アフィリエイト</th>
              <th>案件（プログラム）</th>
              <th>報酬額</th>
              <th>状態</th>
            </tr>
          </thead>
          <tbody>
              {visibleRows.map((transaction) => (
              <tr key={transaction.transaction_id}>
                {showAdvanced ? <td data-label="成果の識別番号">{transaction.transaction_id}</td> : null}
                <td data-label="発生日時">{transaction.occurred_at ? formatDateTime(transaction.occurred_at) : "-"}</td>
                <td data-label="アフィリエイト">{transaction.affiliate_name}</td>
                <td data-label="案件（プログラム）">{transaction.program_name}</td>
                <td data-label="報酬額">{formatCurrency(transaction.reward_amount)}</td>
                <td data-label="状態">{transaction.state}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > visibleCount ? (
        <div className="detail-load-more">
          <ActionButton onClick={() => setVisibleCount((current) => current + 20)}>さらに表示する</ActionButton>
        </div>
      ) : null}
    </>
  );
}

export function AlertDetailScreen({ caseKey, viewerUserId, returnTo }: AlertDetailScreenProps) {
  const [data, setData] = useState<AlertDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submittingStatus, setSubmittingStatus] = useState<ReviewStatus | null>(null);
  const [assignmentBusy, setAssignmentBusy] = useState(false);
  const [followUpBusyId, setFollowUpBusyId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const reviewDialog = useReviewReasonDialog(submittingStatus !== null);
  const { showAdvanced, setShowAdvanced } = useConsoleDisplayMode();
  const resolvedReturnTo = sanitizeReturnTo(returnTo);

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

  const followUpTasks = useMemo(() => data?.follow_up_tasks ?? [], [data?.follow_up_tasks]);
  const relatedCases = useMemo(() => data?.related_cases ?? [], [data?.related_cases]);

  const openReviewDialog = useCallback(
    (status: ReviewStatus) => {
      reviewDialog.openReviewDialog(status);
      setWarning(null);
    },
    [reviewDialog],
  );

  useEffect(() => {
    function isTypingTarget(target: EventTarget | null) {
      if (!(target instanceof HTMLElement)) {
        return false;
      }
      return Boolean(target.closest("input, textarea, select, button, [contenteditable='true']"));
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (reviewDialog.reviewStatus !== null || isTypingTarget(event.target)) {
        return;
      }
      const key = event.key.toLowerCase();
      if (key === "f") {
        event.preventDefault();
        openReviewDialog("confirmed_fraud");
      } else if (key === "w") {
        event.preventDefault();
        openReviewDialog("white");
      } else if (key === "i") {
        event.preventDefault();
        openReviewDialog("investigating");
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [openReviewDialog, reviewDialog.reviewStatus]);

  async function submitReview() {
    if (reviewDialog.reviewStatus === null) {
      return;
    }

    const reason = reviewDialog.validateReviewReason();
    if (!reason) {
      return;
    }

    setSubmittingStatus(reviewDialog.reviewStatus);
    setError(null);
    setWarning(null);
    reviewDialog.clearReviewReasonError();
    try {
      const result = await reviewAlerts([caseKey], reviewDialog.reviewStatus, reason);
      setData((current) => (current ? { ...current, status: result.status } : current));
      reviewDialog.closeReviewDialog();
      setFeedback(`${result.updated_count}件のケースを更新しました。`);
      setWarning(result.missing_keys.length > 0 ? `見つからなかったケースがあります：${result.missing_keys.join("、")}` : null);
      await loadDetail();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "判定結果の更新に失敗しました。");
    } finally {
      setSubmittingStatus(null);
    }
  }

  async function handleAssignment(action: "claim" | "release") {
    setAssignmentBusy(true);
    setError(null);
    setWarning(null);
    try {
      await assignAlerts([caseKey], action);
      setFeedback(action === "claim" ? "担当を自分に設定しました。" : "担当を解除しました。");
      await loadDetail();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "担当者の更新に失敗しました。");
    } finally {
      setAssignmentBusy(false);
    }
  }

  async function handleFollowUp(taskId: string, status: "open" | "completed") {
    setFollowUpBusyId(taskId);
    setError(null);
    setWarning(null);
    try {
      await updateFollowUpTask(taskId, status);
      setFeedback(status === "completed" ? "対応を完了しました。" : "対応を未完了に戻しました。");
      await loadDetail();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "対応状況の更新に失敗しました。");
    } finally {
      setFollowUpBusyId(null);
    }
  }

  const isAssignedToViewer = data?.assignee?.user_id === viewerUserId;

  return (
    <div className="screen-page">
      <PageHeader
        title="アラート詳細"
        description={data?.latest_detected_at ? `最終検知日時：${formatDateTime(data.latest_detected_at)}` : "ケースの詳細情報"}
        actions={
          <Link className="button button-default" href={resolvedReturnTo}>
            アラート一覧に戻る
          </Link>
        }
      />

      {loading && !data ? <LoadingState /> : null}
      {error && !data ? <ErrorState message={error} /> : null}

      {data ? (
        <div className="detail-layout">
          <div className="detail-main">
            <section className="detail-header-grid" aria-label="アラートの概要">
              <div className="detail-summary-card detail-stat-wide">
                <div className="detail-summary-header">
                  <div>
                    <div className="detail-key">主な対象</div>
                    <div className="detail-value">{data.affected_affiliates[0]?.name ?? data.environment.ipaddress ?? "ケース"}</div>
                    <div className="detail-subvalue">{data.affected_programs[0]?.name ?? data.primary_reason}</div>
                  </div>
                  <div className="detail-summary-badges">
                    <RiskBadge score={data.risk_score} level={data.risk_level} emphasized />
                    <StatusBadge status={data.status} />
                  </div>
                </div>
                <div className="detail-summary-grid">
                  <div className="detail-summary-item">
                    <span className="detail-summary-label">検知理由</span>
                    <span className="detail-summary-text">{data.primary_reason}</span>
                  </div>
                  <div className="detail-summary-item">
                    <span className="detail-summary-label">{showAdvanced ? "アクセス情報" : "検知日"}</span>
                    <span className="detail-summary-text">
                      {showAdvanced
                        ? `${data.environment.date ?? "日付なし"} / ${data.environment.ipaddress ?? "IPアドレスなし"}`
                        : data.environment.date ?? "日付なし"}
                    </span>
                  </div>
                </div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">リスクスコア</div>
                <div className="detail-value">{data.risk_score}</div>
                <div className="detail-subvalue">該当した検知ルールの合計点</div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">想定被害額</div>
                <div className="detail-value">{formatCurrency(data.reward_amount)}</div>
                <div className="detail-subvalue">
                  {rewardSourceLabel(data.reward_amount_source, data.reward_amount_is_estimated)}
                </div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">現在の担当者</div>
                <div className="detail-value detail-value-small">{data.assignee?.user_id ?? "未割り当て"}</div>
                <div className="detail-subvalue">
                  {data.assignee?.assigned_at ? `担当開始：${formatDateTime(data.assignee.assigned_at)}` : "担当者は設定されていません"}
                </div>
              </div>
              <div className="detail-stat">
                <div className="detail-key">過去30日の関連ケース</div>
                <div className="detail-value">{relatedCases.length}</div>
                <div className="detail-subvalue">同じアクセス元（IPアドレスとブラウザ情報）で別日に発生したケース</div>
              </div>
            </section>

            <Panel title="検知理由" description={data.primary_reason}>
              {data.reasons.length === 0 ? (
                <EmptyState message="検知理由の記録はありません。" />
              ) : (
                <ul className="reasons-list">
                  {data.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
            </Panel>

            <Panel title="関連する対象" className="detail-panel-compact">
              <div className="detail-related-grid">
                <div className="detail-related-block">
                  <h3 className="detail-section-title">対象アフィリエイト</h3>
                  {renderEntityList(data.affected_affiliates, { linkToAlerts: true, showAdvanced })}
                </div>
                <div className="detail-related-block">
                  <h3 className="detail-section-title">対象の案件（プログラム）</h3>
                  {renderEntityList(data.affected_programs, { showAdvanced })}
                </div>
              </div>
            </Panel>

            <Panel
              title="根拠となる成果データ"
              description="同じ日・同じIPアドレス・同じブラウザ情報に絞った、判定の根拠となるデータです。"
            >
              <TransactionsTable ariaLabel="根拠となる成果データ" rows={data.evidence_transactions} showAdvanced={showAdvanced} />
            </Panel>

            <Panel title="判定履歴" description="このケースに対する判定操作の履歴です。">
              {data.review_history.length === 0 ? (
                <EmptyState message="判定の履歴はまだありません。" />
              ) : (
                <div className="table-wrap detail-table-wrap">
                  <table aria-label="判定履歴" className="detail-data-table">
                    <thead>
                      <tr>
                        <th>判定結果</th>
                        <th>理由</th>
                        <th>判定した人</th>
                        <th>判定日時</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.review_history.map((item) => (
                        <tr key={`${item.reviewed_at}-${item.request_id}-${item.status}`}>
                          <td data-label="判定結果">
                            <StatusBadge status={item.status} />
                          </td>
                          <td data-label="理由">{item.reason || "-"}</td>
                          <td data-label="判定した人">{item.reviewed_by}</td>
                          <td data-label="判定日時">{item.reviewed_at ? formatDateTime(item.reviewed_at) : "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>

            {followUpTasks.length > 0 ? (
              <Panel title="この後の対応" description="不正確定後に確実に行うべき対応の一覧です。">
                <ul className="detail-followup-list">
                  {followUpTasks.map((task) => (
                    <li key={task.id} className="detail-followup-item">
                      <div>
                        <div className="detail-followup-label">{task.label}</div>
                        <div className="detail-followup-meta">
                          {task.status === "completed"
                            ? `完了：${task.completed_by ?? "-"} / ${task.completed_at ? formatDateTime(task.completed_at) : "-"}`
                            : `登録：${task.created_at ? formatDateTime(task.created_at) : "-"} `}
                          {task.due_at
                            ? ` / 期限：${formatDateTime(task.due_at)}${task.is_overdue ? "（期限を過ぎています）" : ""}`
                            : ""}
                        </div>
                      </div>
                      <ActionButton
                        tone={task.status === "completed" ? "default" : "warning"}
                        disabled={followUpBusyId === task.id}
                        onClick={() => void handleFollowUp(task.id, task.status === "completed" ? "open" : "completed")}
                      >
                        {task.status === "completed" ? "未完了に戻す" : "完了にする"}
                      </ActionButton>
                    </li>
                  ))}
                </ul>
              </Panel>
            ) : null}

            {relatedCases.length > 0 ? (
              <Panel title="関連する過去のケース" description="同じアクセス元（IPアドレスとブラウザ情報）で過去に発生したケースです。日をまたぐ不正パターンの確認に役立ちます。">
                <ul className="detail-related-cases">
                  {relatedCases.map((item) => (
                    <li key={item.case_key} className="detail-related-case">
                      <Link className="table-link" href={buildAlertDetailHref(item.case_key, resolvedReturnTo)}>
                        <span className="table-primary">{item.display_label}</span>
                        <span className="table-secondary">
                          {showAdvanced
                            ? item.secondary_label
                            : item.latest_detected_at
                              ? `最終検知日時：${formatDateTime(item.latest_detected_at)}`
                              : "関連ケース"}
                        </span>
                      </Link>
                      <div className="detail-summary-badges">
                        <RiskBadge score={item.risk_score} level={item.risk_level} />
                        <StatusBadge status={item.status} />
                      </div>
                    </li>
                  ))}
                </ul>
              </Panel>
            ) : null}

            {showAdvanced && data.affiliate_recent_transactions.length > 0 ? (
              <Panel
                title="対象アフィリエイトの最近の成果"
                description={`対象アフィリエイトに関する参考情報です。${data.affiliate_recent_scope?.name ? `代表：${data.affiliate_recent_scope.name}` : ""}`}
              >
                <TransactionsTable
                  ariaLabel="対象アフィリエイトの最近の成果"
                  rows={data.affiliate_recent_transactions}
                  showAdvanced={showAdvanced}
                />
              </Panel>
            ) : null}
          </div>

          <div className="detail-sidebar">
            <div className="detail-action-panel">
              <Link className="button button-default button-wide" href={resolvedReturnTo}>
                アラート一覧に戻る
              </Link>
            </div>

            <div className="detail-action-panel">
              <p className="detail-action-title">判定の操作</p>
              <ActionButton
                tone="danger"
                className="button-wide"
                disabled={submittingStatus !== null}
                onClick={() => openReviewDialog("confirmed_fraud")}
              >
                不正と確定
              </ActionButton>
              <ActionButton
                className="button-wide"
                disabled={submittingStatus !== null}
                onClick={() => openReviewDialog("white")}
              >
                正常（ホワイト）と確定
              </ActionButton>
              <ActionButton
                tone="warning"
                className="button-wide"
                disabled={submittingStatus !== null}
                onClick={() => openReviewDialog("investigating")}
              >
                調査中へ変更
              </ActionButton>
              <ActionButton
                className="button-wide"
                disabled={assignmentBusy}
                onClick={() => void handleAssignment(isAssignedToViewer ? "release" : "claim")}
              >
                {isAssignedToViewer ? "担当を外す" : "自分が担当する"}
              </ActionButton>
              <ActionButton className="button-wide" onClick={() => void loadDetail()} disabled={loading}>
                再読み込み
              </ActionButton>
              {showAdvanced ? <p className="table-secondary">キー操作：F で不正確定 / W で正常確定 / I で調査中</p> : null}
            </div>

            {feedback ? (
              <div className="success-message" role="status" aria-live="polite">
                {feedback}
              </div>
            ) : null}
            {warning ? <ErrorState message={warning} /> : null}
            {error ? <ErrorState message={error} /> : null}

            <div className="detail-action-panel">
              <p className="detail-action-title">参考情報</p>
              <div className="detail-meta-block">
                <div className="detail-meta-row">
                  <span>被害額の算出方法</span>
                  <span className="detail-meta-value">
                    {rewardSourceLabel(data.reward_amount_source, data.reward_amount_is_estimated)}
                  </span>
                </div>
                {showAdvanced ? (
                  <div className="detail-meta-row">
                    <span>アクセス元のブラウザ情報</span>
                    <span className="detail-meta-value detail-break">{data.environment.useragent ?? "-"}</span>
                  </div>
                ) : null}
                {showAdvanced ? (
                  <div className="detail-meta-row">
                    <span>ケース識別番号</span>
                    <span className="detail-meta-value detail-break">{data.case_key}</span>
                  </div>
                ) : null}
                {showAdvanced ? (
                  <div className="detail-meta-row">
                    <span>検知記録の識別番号</span>
                    <span className="detail-meta-value detail-break">{data.finding_key}</span>
                  </div>
                ) : null}
              </div>
              {!showAdvanced ? (
                <ActionButton className="button-wide" onClick={() => setShowAdvanced(true)}>
                  詳細表示に切り替える
                </ActionButton>
              ) : null}
            </div>

          </div>
        </div>
      ) : null}

      <ReviewReasonDialog
        open={reviewDialog.reviewStatus !== null}
        title="判定理由の入力"
        description="対応状態を変更する理由を入力してください。"
        confirmLabel={reviewDialog.reviewStatus ? reviewStatusActionLabel(reviewDialog.reviewStatus) : "この内容で登録"}
        confirmTone={reviewDialog.reviewStatus ? reviewStatusConfirmTone(reviewDialog.reviewStatus) : "warning"}
        value={reviewDialog.reviewReason}
        error={reviewDialog.reviewReasonError}
        busy={submittingStatus !== null}
        onChange={reviewDialog.setReviewReasonValue}
        onCancel={reviewDialog.closeReviewDialog}
        onConfirm={() => void submitReview()}
        presets={reviewDialog.reviewStatus ? reviewReasonPresets(reviewDialog.reviewStatus) : []}
        textareaProps={{
          autoFocus: true,
          rows: 5,
          maxLength: 500,
          placeholder: "対応状態を変更する理由を記入してください。",
        }}
      />
    </div>
  );
}
