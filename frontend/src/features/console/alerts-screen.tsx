"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import {
  ActionButton,
  EmptyState,
  ErrorState,
  LoadingState,
  RiskBadge,
  StatusBadge,
  StatusCountStrip,
} from "@/components/console-ui";
import { buildAlertsCsvUrl, getAlerts, reviewAlerts } from "@/lib/console-api";
import type {
  AlertFilterStatus,
  AlertListItem,
  AlertRiskFilter,
  AlertsResponse,
  ReviewStatus,
} from "@/lib/console-types";
import type { ConsoleViewerRole } from "@/lib/console-viewer";
import { formatCurrency, formatDateTime } from "@/lib/format";

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
  viewerRole: ConsoleViewerRole;
};

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
  return `${items[0]?.name ?? items[0]?.id} ほか${items.length - 1}件`;
}

function programPreview(item: AlertListItem) {
  if (item.affected_programs.length === 0) {
    return "なし";
  }
  if (item.affected_programs.length === 1) {
    return item.affected_programs[0]?.name ?? item.affected_programs[0]?.id ?? "なし";
  }
  return `${item.affected_programs[0]?.name ?? item.affected_programs[0]?.id} ほか${item.affected_programs.length - 1}件`;
}

function promptReviewReason() {
  const reason = globalThis.prompt?.("レビュー理由を入力してください。");
  return reason?.trim() ?? "";
}

export function AlertsScreen({ searchParams, viewerRole }: AlertsScreenProps) {
  const routeFilters = useMemo(() => buildInitialFilters(searchParams), [searchParams]);
  const [draftFilters, setDraftFilters] = useState(routeFilters);
  const [data, setData] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [submittingStatus, setSubmittingStatus] = useState<ReviewStatus | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const { replace } = useRouter();
  const pathname = usePathname();

  const loadAlerts = useCallback(async (filters: AlertFilters) => {
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
      const canonicalFilters = filtersFromResponse(response);
      if (toFilterQuery(filters) !== toFilterQuery(canonicalFilters)) {
        replace(`${pathname}?${toFilterQuery(canonicalFilters)}`, { scroll: false });
      }
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "アラート一覧の取得に失敗しました。");
    } finally {
      setLoading(false);
    }
  }, [pathname, replace]);

  useEffect(() => {
    setDraftFilters(routeFilters);
    void loadAlerts(routeFilters);
  }, [loadAlerts, routeFilters]);

  function setDraftFilter<K extends keyof AlertFilters>(key: K, value: AlertFilters[K]) {
    setDraftFilters((current) => ({ ...current, [key]: value }));
  }

  function replaceRoute(nextFilters: AlertFilters) {
    setFeedback(null);
    setWarning(null);
    replace(`${pathname}?${toFilterQuery(nextFilters)}`, { scroll: false });
  }

  async function handleBulkAction(status: ReviewStatus) {
    if (selectedKeys.length === 0) {
      return;
    }
    const reason = promptReviewReason();
    if (!reason) {
      setWarning("レビュー理由を入力しない限り更新できません。");
      return;
    }

    setSubmittingStatus(status);
    setError(null);
    setWarning(null);
    try {
      const result = await reviewAlerts(selectedKeys, status, reason);
      setFeedback(`${result.updated_count}件のケースを更新しました。`);
      setWarning(result.missing_keys.length > 0 ? `見つからないケース: ${result.missing_keys.join(", ")}` : null);
      await loadAlerts(routeFilters);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "レビュー更新に失敗しました。");
    } finally {
      setSubmittingStatus(null);
    }
  }

  const items = data?.items ?? [];
  const allSelected = items.length > 0 && selectedKeys.length === items.length;
  const activeFilters = data ? filtersFromResponse(data) : routeFilters;
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / activeFilters.pageSize));
  const exportUrl = buildAlertsCsvUrl({
    status: activeFilters.status,
    riskLevel: activeFilters.riskLevel !== "all" ? activeFilters.riskLevel : undefined,
    startDate: activeFilters.startDate,
    endDate: activeFilters.endDate,
    search: activeFilters.search,
    sort: activeFilters.sort,
  });

  return (
    <div className="alerts-page">
      <div className="alerts-topbar">
        <div className="alerts-topbar-left">
          <h1 className="alerts-title">アラート一覧</h1>
          {data ? <StatusCountStrip counts={data.status_counts} /> : null}
          <p className="table-secondary">件数は現在の絞り込み条件内です。</p>
        </div>
        <div className="alerts-topbar-right">
          <a className="button button-default" href={exportUrl}>
            CSV出力
          </a>
        </div>
      </div>

      <div className="alerts-filters">
        <div className="alerts-filters-fields">
          <div className="form-field form-field--compact">
            <label htmlFor="alert-status">状態</label>
            <select
              id="alert-status"
              aria-label="状態"
              value={draftFilters.status}
              onChange={(event) => setDraftFilter("status", event.target.value as AlertFilterStatus)}
            >
              <option value="unhandled">未対応</option>
              <option value="investigating">調査中</option>
              <option value="confirmed_fraud">不正</option>
              <option value="white">ホワイト</option>
              <option value="all">すべて</option>
            </select>
          </div>

          <div className="form-field form-field--compact">
            <label htmlFor="alert-risk-level">リスク</label>
            <select
              id="alert-risk-level"
              aria-label="リスクレベル"
              value={draftFilters.riskLevel}
              onChange={(event) => setDraftFilter("riskLevel", event.target.value as AlertRiskFilter)}
            >
              <option value="all">すべて</option>
              <option value="critical">最優先</option>
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>

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
              placeholder="affiliate、IP、UA"
            />
          </div>

          <div className="alerts-filters-actions">
            <ActionButton onClick={() => replaceRoute({ ...draftFilters, page: 1 })} disabled={loading}>
              絞り込む
            </ActionButton>
            <ActionButton onClick={() => replaceRoute(DEFAULT_FILTERS)} disabled={loading}>
              リセット
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

      {viewerRole === "admin" && selectedKeys.length > 0 ? (
        <div className="selection-bar">
          <span className="selection-bar-count">{selectedKeys.length}件選択中</span>
          <div className="selection-bar-actions">
            <ActionButton
              tone="danger"
              disabled={submittingStatus !== null}
              onClick={() => void handleBulkAction("confirmed_fraud")}
            >
              不正にする
            </ActionButton>
            <ActionButton
              disabled={submittingStatus !== null}
              onClick={() => void handleBulkAction("white")}
            >
              ホワイトにする
            </ActionButton>
            <ActionButton
              tone="warning"
              disabled={submittingStatus !== null}
              onClick={() => void handleBulkAction("investigating")}
            >
              調査中にする
            </ActionButton>
          </div>
        </div>
      ) : null}

      {loading && !data ? <LoadingState /> : null}

      <div className="alerts-table-area">
        {error && data ? <ErrorState message={error} /> : null}
        {loading && data ? <LoadingState message="アラートを更新しています..." /> : null}
        {!loading && items.length === 0 ? (
          <EmptyState
            message={activeFilters.search ? "条件に一致するアラートはありません。" : "対象期間のアラートはありません。"}
          />
        ) : (
          <table aria-label="不正アラート一覧" className="table-sticky-head">
            <thead>
              <tr>
                <th>
                  <input
                    aria-label="すべて選択"
                    type="checkbox"
                    checked={allSelected}
                    onChange={() => setSelectedKeys(allSelected ? [] : items.map((item) => item.case_key))}
                  />
                </th>
                <th>リスク</th>
                <th>影響affiliate</th>
                <th>環境</th>
                <th>状態</th>
                <th>想定被害</th>
                <th>検知日時</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.case_key}>
                  <td>
                    <input
                      aria-label={`${namedPreview(item.affected_affiliates)} を選択`}
                      type="checkbox"
                      checked={selectedKeys.includes(item.case_key)}
                      onChange={() =>
                        setSelectedKeys((current) =>
                          current.includes(item.case_key)
                            ? current.filter((value) => value !== item.case_key)
                            : [...current, item.case_key],
                        )
                      }
                    />
                  </td>
                  <td>
                    <RiskBadge score={item.risk_score} level={item.risk_level} />
                  </td>
                  <td>
                    <Link className="table-link" href={`/alerts/${item.case_key}`}>
                      <span className="table-primary">{namedPreview(item.affected_affiliates)}</span>
                      <span className="table-secondary">{`${item.affected_affiliate_count}件 / ${programPreview(item)}`}</span>
                      <span className="table-tertiary">{item.primary_reason}</span>
                    </Link>
                  </td>
                  <td>
                    <div className="table-link">
                      <span className="table-primary">{item.environment.ipaddress ?? "IPなし"}</span>
                      <span className="table-secondary">{item.environment.useragent ?? "UAなし"}</span>
                      <span className="table-tertiary">{item.environment.date ?? "日付なし"}</span>
                    </div>
                  </td>
                  <td>
                    <StatusBadge status={item.status} />
                  </td>
                  <td>
                    <div className="amount-cell">
                      <span>{formatCurrency(item.reward_amount)}</span>
                      <span className={`meta-badge ${item.reward_amount_is_estimated ? "meta-badge-warning" : "meta-badge-muted"}`}>
                        {item.reward_amount_is_estimated ? "推定" : "実測"}
                      </span>
                    </div>
                  </td>
                  <td>{item.latest_detected_at ? formatDateTime(item.latest_detected_at) : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data ? (
        <div className="alerts-pagination">
          <span className="table-secondary">
            {total}件中 {(activeFilters.page - 1) * activeFilters.pageSize + (items.length > 0 ? 1 : 0)}-
            {(activeFilters.page - 1) * activeFilters.pageSize + items.length}件
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
