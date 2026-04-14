"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useConsoleDisplayMode } from "@/components/console-display-mode";
import {
  ActionButton,
  EmptyState,
  ErrorState,
  LoadingState,
  ReviewReasonDialog,
  RiskBadge,
  StatusBadge,
  StatusCountStrip,
} from "@/components/console-ui";
import { buildAlertsCsvUrl, getAlerts, reviewAlerts, reviewAlertsByFilter } from "@/lib/console-api";
import type {
  AlertFilterStatus,
  AlertListItem,
  AlertRiskFilter,
  AlertsResponse,
  ReviewStatus,
} from "@/lib/console-types";
import { formatCurrency, formatDateTime } from "@/lib/format";
import {
  reviewReasonPresets,
  reviewStatusActionLabel,
  reviewStatusConfirmTone,
  useReviewReasonDialog,
} from "./review-reason-dialog";

type AlertFilters = {
  status: AlertFilterStatus;
  riskLevel: AlertRiskFilter;
  startDate: string;
  endDate: string;
  search: string;
  sort: string;
  page: number;
  pageSize: number;
};

const DEFAULT_FILTERS: AlertFilters = {
  status: "unhandled",
  riskLevel: "all",
  startDate: "",
  endDate: "",
  search: "",
  sort: "risk_desc",
  page: 1,
  pageSize: 50,
};

type AlertsScreenProps = {
  searchParams?: Record<string, string | string[] | undefined>;
};

type ReviewScope = "selected" | "filtered";

function firstSearchParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

function buildInitialFilters(searchParams?: Record<string, string | string[] | undefined>): AlertFilters {
  if (!searchParams) {
    return DEFAULT_FILTERS;
  }
  const page = Number(firstSearchParam(searchParams.page) || DEFAULT_FILTERS.page);
  const pageSize = Number(firstSearchParam(searchParams.page_size) || DEFAULT_FILTERS.pageSize);
  return {
    status: (firstSearchParam(searchParams.status) || DEFAULT_FILTERS.status) as AlertFilterStatus,
    riskLevel: (firstSearchParam(searchParams.risk_level) || DEFAULT_FILTERS.riskLevel) as AlertRiskFilter,
    startDate: firstSearchParam(searchParams.start_date),
    endDate: firstSearchParam(searchParams.end_date),
    search: firstSearchParam(searchParams.search),
    sort: firstSearchParam(searchParams.sort) || DEFAULT_FILTERS.sort,
    page: Number.isFinite(page) && page > 0 ? page : DEFAULT_FILTERS.page,
    pageSize: Number.isFinite(pageSize) && pageSize > 0 ? pageSize : DEFAULT_FILTERS.pageSize,
  };
}

function toFilterQuery(filters: AlertFilters) {
  const query = new URLSearchParams();
  query.set("status", filters.status);
  query.set("sort", filters.sort);
  query.set("page", String(filters.page));
  query.set("page_size", String(filters.pageSize));
  if (filters.riskLevel !== "all") {
    query.set("risk_level", filters.riskLevel);
  }
  if (filters.startDate) {
    query.set("start_date", filters.startDate);
  }
  if (filters.endDate) {
    query.set("end_date", filters.endDate);
  }
  if (filters.search.trim()) {
    query.set("search", filters.search.trim());
  }
  return query.toString();
}

function filtersFromResponse(response: AlertsResponse): AlertFilters {
  return {
    status: response.applied_filters.status as AlertFilterStatus,
    riskLevel: (response.applied_filters.risk_level ?? "all") as AlertRiskFilter,
    startDate: response.applied_filters.start_date ?? "",
    endDate: response.applied_filters.end_date ?? "",
    search: response.applied_filters.search ?? "",
    sort: response.applied_filters.sort,
    page: response.page,
    pageSize: response.page_size,
  };
}

function namedPreview(items: AlertListItem["affected_affiliates"]) {
  if (items.length === 0) {
    return "なし";
  }
  if (items.length === 1) {
    return items[0]?.name ?? items[0]?.id ?? "なし";
  }
  return `${items[0]?.name ?? items[0]?.id} 他${items.length - 1}件`;
}

function programPreview(item: AlertListItem) {
  if (item.affected_programs.length === 0) {
    return "なし";
  }
  if (item.affected_programs.length === 1) {
    return item.affected_programs[0]?.name ?? item.affected_programs[0]?.id ?? "なし";
  }
  return `${item.affected_programs[0]?.name ?? item.affected_programs[0]?.id} 他${item.affected_programs.length - 1}件`;
}

function buildAlertDetailHref(caseKey: string, returnTo: string) {
  const searchParams = new URLSearchParams();
  searchParams.set("returnTo", returnTo);
  return `/alerts/${encodeURIComponent(caseKey)}?${searchParams.toString()}`;
}

export function AlertsScreen({ searchParams }: AlertsScreenProps) {
  const routeFilters = useMemo(() => buildInitialFilters(searchParams), [searchParams]);
  const [draftFilters, setDraftFilters] = useState(routeFilters);
  const [data, setData] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [submittingStatus, setSubmittingStatus] = useState<ReviewStatus | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [reviewScope, setReviewScope] = useState<ReviewScope>("selected");
  const [activeIndex, setActiveIndex] = useState(0);
  const rowLinkRefs = useRef<Array<HTMLAnchorElement | null>>([]);
  const { replace } = useRouter();
  const pathname = usePathname();
  const reviewDialog = useReviewReasonDialog(submittingStatus !== null);
  const { showAdvanced } = useConsoleDisplayMode();

  const loadAlerts = useCallback(
    async (filters: AlertFilters) => {
      setLoading(true);
      setError(null);
      try {
        const response = await getAlerts({
          status: filters.status,
          riskLevel: filters.riskLevel !== "all" ? filters.riskLevel : undefined,
          startDate: filters.startDate,
          endDate: filters.endDate,
          search: filters.search,
          sort: filters.sort,
          page: filters.page,
          pageSize: filters.pageSize,
        });
        setData(response);
        setSelectedKeys([]);
        setReviewScope("selected");
        const canonicalFilters = filtersFromResponse(response);
        if (toFilterQuery(filters) !== toFilterQuery(canonicalFilters)) {
          replace(`${pathname}?${toFilterQuery(canonicalFilters)}`, { scroll: false });
        }
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : "アラートの取得に失敗しました。");
      } finally {
        setLoading(false);
      }
    },
    [pathname, replace],
  );

  useEffect(() => {
    setDraftFilters(routeFilters);
    void loadAlerts(routeFilters);
  }, [loadAlerts, routeFilters]);

  useEffect(() => {
    if (!data?.items.length) {
      setActiveIndex(0);
      return;
    }
    setActiveIndex((current) => Math.min(current, data.items.length - 1));
  }, [data?.items.length]);

  function setDraftFilter<K extends keyof AlertFilters>(key: K, value: AlertFilters[K]) {
    setDraftFilters((current) => ({ ...current, [key]: value }));
  }

  function replaceRoute(nextFilters: AlertFilters) {
    setFeedback(null);
    setWarning(null);
    replace(`${pathname}?${toFilterQuery(nextFilters)}`, { scroll: false });
  }

  function openBulkAction(status: ReviewStatus) {
    if (reviewScope === "selected" && selectedKeys.length === 0) {
      return;
    }
    if (reviewScope === "filtered" && total === 0) {
      return;
    }
    reviewDialog.openReviewDialog(status);
    setWarning(null);
  }

  async function submitBulkAction() {
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
      const result =
        reviewScope === "filtered"
          ? await reviewAlertsByFilter(
              {
                status: activeFilters.status,
                riskLevel: activeFilters.riskLevel !== "all" ? activeFilters.riskLevel : undefined,
                startDate: activeFilters.startDate,
                endDate: activeFilters.endDate,
                search: activeFilters.search,
                sort: activeFilters.sort,
              },
              reviewDialog.reviewStatus,
              reason,
            )
          : await reviewAlerts(selectedKeys, reviewDialog.reviewStatus, reason);
      reviewDialog.closeReviewDialog();
      setFeedback(
        reviewScope === "filtered"
          ? `絞り込み条件に合う${result.updated_count}件のケースを更新しました。`
          : `${result.updated_count}件のケースを更新しました。`,
      );
      setWarning(result.missing_keys.length > 0 ? `見つからなかったケースがあります：${result.missing_keys.join("、")}` : null);
      await loadAlerts(routeFilters);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "判定結果の更新に失敗しました。");
    } finally {
      setSubmittingStatus(null);
    }
  }

  const items = useMemo(() => data?.items ?? [], [data?.items]);
  const allSelected = items.length > 0 && selectedKeys.length === items.length;
  const activeFilters = data ? filtersFromResponse(data) : routeFilters;
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / activeFilters.pageSize));
  const currentListHref = `${pathname}?${toFilterQuery(activeFilters)}`;
  const exportUrl = buildAlertsCsvUrl({
    status: activeFilters.status,
    riskLevel: activeFilters.riskLevel !== "all" ? activeFilters.riskLevel : undefined,
    startDate: activeFilters.startDate,
    endDate: activeFilters.endDate,
    search: activeFilters.search,
    sort: activeFilters.sort,
  });
  const pageStart = (activeFilters.page - 1) * activeFilters.pageSize + (items.length > 0 ? 1 : 0);
  const pageEnd = (activeFilters.page - 1) * activeFilters.pageSize + items.length;
  const selectionCount = reviewScope === "filtered" ? total : selectedKeys.length;
  const showSelectionBar = reviewScope === "filtered" || selectedKeys.length > 0 || (showAdvanced && total > 0);

  useEffect(() => {
    function isTypingTarget(target: EventTarget | null) {
      if (!(target instanceof HTMLElement)) {
        return false;
      }
      return Boolean(target.closest("input, textarea, select, button, [contenteditable='true']"));
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (reviewDialog.reviewStatus !== null || isTypingTarget(event.target) || items.length === 0) {
        return;
      }

      if (event.key === "j" || event.key === "k") {
        event.preventDefault();
        const delta = event.key === "j" ? 1 : -1;
        setActiveIndex((current) => {
          const nextIndex = Math.max(0, Math.min(items.length - 1, current + delta));
          rowLinkRefs.current[nextIndex]?.focus();
          return nextIndex;
        });
        return;
      }

      if (event.key.toLowerCase() === "x") {
        event.preventDefault();
        const caseKey = items[activeIndex]?.case_key;
        if (!caseKey) {
          return;
        }
        setReviewScope("selected");
        setSelectedKeys((current) =>
          current.includes(caseKey) ? current.filter((value) => value !== caseKey) : [...current, caseKey],
        );
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [activeIndex, items, reviewDialog.reviewStatus]);

  return (
    <div className="alerts-page">
      <div className="alerts-topbar">
        <div className="alerts-topbar-left">
          <h1 className="alerts-title">アラート一覧</h1>
          {data ? <StatusCountStrip counts={data.status_counts} /> : null}
          <p className="table-secondary">初期表示では全期間の最新ケースを表示します。</p>
          {showAdvanced ? <p className="table-secondary">キー操作：J/K で行の移動、X でチェックの切り替え</p> : null}
        </div>
        {showAdvanced ? (
          <div className="alerts-topbar-right">
            <a className="button button-default" href={exportUrl}>
              CSV形式でダウンロード
            </a>
          </div>
        ) : null}
      </div>

      <div className="alerts-filters">
        <div className="alerts-filters-fields">
          <div className="form-field form-field--compact">
            <label htmlFor="alert-status">対応状態</label>
            <select
              id="alert-status"
              aria-label="対応状態"
              value={draftFilters.status}
              onChange={(event) => setDraftFilter("status", event.target.value as AlertFilterStatus)}
            >
              <option value="unhandled">未対応</option>
              <option value="investigating">調査中</option>
              <option value="confirmed_fraud">不正確定</option>
              <option value="white">ホワイト</option>
              <option value="all">すべて</option>
            </select>
          </div>

          <div className="form-field form-field--compact">
            <label htmlFor="alert-risk-level">リスクレベル</label>
            <select
              id="alert-risk-level"
              aria-label="リスクレベル"
              value={draftFilters.riskLevel}
              onChange={(event) => setDraftFilter("riskLevel", event.target.value as AlertRiskFilter)}
            >
              <option value="all">すべて</option>
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>

          <div className="form-field form-field--compact">
            <label htmlFor="alert-sort">並び順</label>
            <select
              id="alert-sort"
              aria-label="並び順"
              value={draftFilters.sort}
              onChange={(event) => setDraftFilter("sort", event.target.value)}
            >
              <option value="risk_desc">リスク高い順</option>
              <option value="risk_asc">リスク低い順</option>
              <option value="damage_desc">被害額高い順</option>
              <option value="damage_asc">被害額低い順</option>
              <option value="detected_desc">新しい順</option>
              <option value="detected_asc">古い順</option>
            </select>
          </div>

          {showAdvanced ? (
            <div className="form-field form-field--compact">
              <label htmlFor="alert-page-size">表示件数</label>
              <select
                id="alert-page-size"
                aria-label="表示件数"
                value={draftFilters.pageSize}
                onChange={(event) => setDraftFilter("pageSize", Number(event.target.value))}
              >
                <option value={50}>50件</option>
                <option value={100}>100件</option>
                <option value={200}>200件</option>
              </select>
            </div>
          ) : null}

          <div className="form-field form-field--compact">
            <label htmlFor="alert-start-date">開始日</label>
            <input
              id="alert-start-date"
              aria-label="開始日"
              type="date"
              value={draftFilters.startDate}
              onChange={(event) => setDraftFilter("startDate", event.target.value)}
            />
          </div>

          <div className="form-field form-field--compact">
            <label htmlFor="alert-end-date">終了日</label>
            <input
              id="alert-end-date"
              aria-label="終了日"
              type="date"
              value={draftFilters.endDate}
              onChange={(event) => setDraftFilter("endDate", event.target.value)}
            />
          </div>

          <div className="form-field form-field--compact form-field--grow">
            <label htmlFor="alert-search">検索</label>
            <input
              id="alert-search"
              aria-label="検索"
              type="search"
              value={draftFilters.search}
              onChange={(event) => setDraftFilter("search", event.target.value)}
              placeholder={showAdvanced ? "アフィリエイト名、案件名、IPアドレス、ブラウザ情報、検知理由" : "アフィリエイト名、案件名、検知理由"}
            />
          </div>

          <div className="alerts-filters-actions">
            <ActionButton onClick={() => replaceRoute({ ...draftFilters, page: 1 })} disabled={loading}>
              この条件で絞り込む
            </ActionButton>
            <ActionButton onClick={() => replaceRoute(DEFAULT_FILTERS)} disabled={loading}>
              条件を初期状態に戻す
            </ActionButton>
          </div>
        </div>
      </div>

      {feedback ? (
        <div className="success-message" role="status" aria-live="polite">
          {feedback}
        </div>
      ) : null}
      {warning ? <ErrorState message={warning} /> : null}
      {error && !data ? <ErrorState message={error} /> : null}

      {showSelectionBar ? (
        <div className="selection-bar">
          <span className="selection-bar-count">
            {reviewScope === "filtered" ? `絞り込み条件に合う全 ${selectionCount} 件を対象にします` : `${selectionCount}件を選択中`}
          </span>
          <div className="selection-bar-actions">
            {showAdvanced && reviewScope === "selected" && total > items.length ? (
              <ActionButton onClick={() => setReviewScope("filtered")} disabled={loading || total === 0}>
                絞り込み全件を対象にする
              </ActionButton>
            ) : null}
            {showAdvanced && reviewScope === "filtered" ? (
              <ActionButton onClick={() => setReviewScope("selected")} disabled={loading}>
                選択したケースだけに戻す
              </ActionButton>
            ) : null}
            <ActionButton tone="danger" disabled={submittingStatus !== null || selectionCount === 0} onClick={() => openBulkAction("confirmed_fraud")}>
              不正と確定
            </ActionButton>
            <ActionButton disabled={submittingStatus !== null || selectionCount === 0} onClick={() => openBulkAction("white")}>
              正常（ホワイト）と確定
            </ActionButton>
            <ActionButton tone="warning" disabled={submittingStatus !== null || selectionCount === 0} onClick={() => openBulkAction("investigating")}>
              調査中へ変更
            </ActionButton>
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
        onConfirm={() => void submitBulkAction()}
        presets={reviewDialog.reviewStatus ? reviewReasonPresets(reviewDialog.reviewStatus) : []}
        textareaProps={{
          autoFocus: true,
          rows: 5,
          maxLength: 500,
          placeholder: "対応状態を変更する理由を記入してください。",
        }}
      />

      {loading && !data ? <LoadingState /> : null}

      <div className="alerts-table-area">
        {error && data ? <ErrorState message={error} /> : null}
        {loading && data ? <LoadingState message="アラート一覧を更新しています..." /> : null}
        {!loading && items.length === 0 ? (
          <EmptyState message={activeFilters.search ? "条件に合うアラートは見つかりませんでした。" : "表示するアラートはありません。"} />
        ) : (
          <table aria-label="不正アラート一覧" className="table-sticky-head">
            <thead>
              <tr>
                <th className="alerts-cell-select">
                  <input
                    aria-label="すべてのアラートを選択する"
                    type="checkbox"
                    checked={allSelected}
                    onChange={() => {
                      setReviewScope("selected");
                      setSelectedKeys(allSelected ? [] : items.map((item) => item.case_key));
                    }}
                  />
                </th>
                <th className="alerts-cell-risk">リスク</th>
                <th className="alerts-cell-affiliate">対象アフィリエイト</th>
                {showAdvanced ? <th className="alerts-cell-environment">アクセス情報</th> : null}
                <th className="alerts-cell-status">状態</th>
                <th className="alerts-cell-amount">想定被害額</th>
                <th className="alerts-cell-detected">検知日時</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={item.case_key} className={activeIndex === index ? "alerts-row-active" : undefined}>
                  <td className="alerts-cell-select" data-label="選択">
                    <input
                      aria-label={`${namedPreview(item.affected_affiliates)}を選択`}
                      type="checkbox"
                      checked={selectedKeys.includes(item.case_key)}
                      onChange={() => {
                        setReviewScope("selected");
                        setSelectedKeys((current) =>
                          current.includes(item.case_key)
                            ? current.filter((value) => value !== item.case_key)
                            : [...current, item.case_key],
                        );
                      }}
                    />
                  </td>
                  <td className="alerts-cell-risk" data-label="リスク">
                    <RiskBadge score={item.risk_score} level={item.risk_level} />
                  </td>
                  <td className="alerts-cell-affiliate" data-label="対象アフィリエイト">
                    <Link
                      ref={(element) => {
                        rowLinkRefs.current[index] = element;
                      }}
                      className="table-link"
                      href={buildAlertDetailHref(item.case_key, currentListHref)}
                      onFocus={() => setActiveIndex(index)}
                    >
                      <span className="table-primary">{item.display_label || namedPreview(item.affected_affiliates)}</span>
                      <span className="table-secondary">{`アフィリエイト ${item.affected_affiliate_count}件 / ${programPreview(item)}`}</span>
                      <span className="table-tertiary">{item.primary_reason}</span>
                      <span className="table-tertiary">{`担当者：${item.assignee?.user_id ?? "未割り当て"} / 未完了の対応 ${item.follow_up_open_count ?? 0}件`}</span>
                    </Link>
                  </td>
                  {showAdvanced ? (
                    <td className="alerts-cell-environment" data-label="アクセス情報">
                      <div className="table-link">
                        <span className="table-primary">{item.environment.ipaddress ?? "IPアドレスなし"}</span>
                        <span className="table-secondary">{item.environment.useragent ?? "ブラウザ情報なし"}</span>
                        <span className="table-tertiary">{item.environment.date ?? "日付なし"}</span>
                      </div>
                    </td>
                  ) : null}
                  <td className="alerts-cell-status" data-label="状態">
                    <StatusBadge status={item.status} />
                  </td>
                  <td className="alerts-cell-amount" data-label="想定被害額">
                    <div className={`amount-cell ${item.reward_amount_is_estimated ? "amount-cell-estimated" : "amount-cell-actual"}`}>
                      <span>{formatCurrency(item.reward_amount)}</span>
                      <span className={`meta-badge ${item.reward_amount_is_estimated ? "meta-badge-warning" : "meta-badge-muted"}`}>
                        {item.reward_amount_is_estimated ? "推定の金額" : "実績の金額"}
                      </span>
                    </div>
                  </td>
                  <td className="alerts-cell-detected" data-label="検知日時">
                    {item.latest_detected_at ? formatDateTime(item.latest_detected_at) : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data ? (
        <div className="alerts-pagination">
          <span className="table-secondary">
            全{total}件のうち {pageStart}〜{pageEnd}件を表示しています
          </span>
          <div className="selection-bar-actions">
            <ActionButton
              disabled={loading || activeFilters.page <= 1}
              onClick={() => replaceRoute({ ...activeFilters, page: activeFilters.page - 1 })}
            >
              前へ
            </ActionButton>
            <span className="table-secondary">
              {activeFilters.page} / {totalPages}
            </span>
            <ActionButton
              disabled={loading || !data.has_next}
              onClick={() => replaceRoute({ ...activeFilters, page: activeFilters.page + 1 })}
            >
              次へ
            </ActionButton>
          </div>
        </div>
      ) : null}
    </div>
  );
}
