"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import {
  ActionButton,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  RiskBadge,
  StatusBadge,
  StatusCountStrip,
} from "@/components/console-ui";
import { getAlerts, reviewAlerts } from "@/lib/console-api";
import type {
  AlertFilterStatus,
  AlertListItem,
  AlertsResponse,
  ReviewStatus,
} from "@/lib/console-types";
import { formatCurrency, formatDateTime } from "@/lib/format";

type AlertFilters = {
  status: AlertFilterStatus;
  startDate: string;
  endDate: string;
  sort: string;
  page: number;
  pageSize: number;
};

const DEFAULT_FILTERS: AlertFilters = {
  status: "unhandled",
  startDate: "",
  endDate: "",
  sort: "risk_desc",
  page: 1,
  pageSize: 50,
};

type AlertGroup = {
  groupKey: string;
  affiliateId: string;
  affiliateName: string;
  detectedAt: string;
  detectedAtLabel: string;
  items: AlertListItem[];
  riskScore: number;
  riskLevel: AlertListItem["risk_level"];
  status: ReviewStatus | null;
  estimatedDamage: number;
  transactionCount: number;
  outcomeSummary: string;
  patternSummary: string;
};

type AlertsScreenProps = {
  searchParams?: Record<string, string | string[] | undefined>;
};

type SelectionCheckboxProps = {
  checked: boolean;
  indeterminate: boolean;
  ariaLabel: string;
  onChange: () => void;
};

function SelectionCheckbox({ checked, indeterminate, ariaLabel, onChange }: SelectionCheckboxProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.indeterminate = indeterminate;
    }
  }, [indeterminate]);

  return (
    <input
      ref={inputRef}
      aria-label={ariaLabel}
      type="checkbox"
      checked={checked}
      onChange={onChange}
    />
  );
}

function firstSearchParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

function buildInitialFilters(searchParams?: Record<string, string | string[] | undefined>): AlertFilters {
  if (!searchParams) {
    return DEFAULT_FILTERS;
  }

  const status = firstSearchParam(searchParams.status);
  const startDate = firstSearchParam(searchParams.start_date);
  const endDate = firstSearchParam(searchParams.end_date);
  const sort = firstSearchParam(searchParams.sort);
  const page = Number(firstSearchParam(searchParams.page) || DEFAULT_FILTERS.page);
  const pageSize = Number(firstSearchParam(searchParams.page_size) || DEFAULT_FILTERS.pageSize);

  return {
    status: (status || DEFAULT_FILTERS.status) as AlertFilterStatus,
    startDate,
    endDate,
    sort: sort || DEFAULT_FILTERS.sort,
    page: Number.isFinite(page) && page > 0 ? page : DEFAULT_FILTERS.page,
    pageSize: Number.isFinite(pageSize) && pageSize > 0 ? pageSize : DEFAULT_FILTERS.pageSize,
  };
}

function parseSearchParamsKey(key: string): Record<string, string | string[] | undefined> {
  if (!key) {
    return {};
  }
  try {
    return JSON.parse(key) as Record<string, string | string[] | undefined>;
  } catch {
    return {};
  }
}

function areFiltersEqual(left: AlertFilters, right: AlertFilters) {
  return (
    left.status === right.status &&
    left.startDate === right.startDate &&
    left.endDate === right.endDate &&
    left.sort === right.sort &&
    left.page === right.page &&
    left.pageSize === right.pageSize
  );
}

function toFilterQuery(filters: AlertFilters) {
  const query = new URLSearchParams();
  query.set("status", filters.status);
  query.set("sort", filters.sort);
  query.set("page", String(filters.page));
  query.set("page_size", String(filters.pageSize));
  if (filters.startDate) {
    query.set("start_date", filters.startDate);
  }
  if (filters.endDate) {
    query.set("end_date", filters.endDate);
  }
  return query.toString();
}

function summarizeOutcomes(items: AlertListItem[]) {
  const uniqueOutcomeTypes = Array.from(new Set(items.map((item) => item.outcome_type)));
  if (uniqueOutcomeTypes.length <= 2) {
    return uniqueOutcomeTypes.join(" / ");
  }
  return `${uniqueOutcomeTypes.slice(0, 2).join(" / ")} 他${uniqueOutcomeTypes.length - 2}件`;
}

function buildAlertGroups(items: AlertListItem[]) {
  const groups: AlertGroup[] = [];
  const groupMap = new Map<string, AlertGroup>();

  for (const item of items) {
    const detectedAtLabel = formatDateTime(item.detected_at);
    const groupKey = `${item.affiliate_id}::${detectedAtLabel}`;
    const existing = groupMap.get(groupKey);

    if (existing) {
      existing.items.push(item);
      existing.estimatedDamage += item.reward_amount;
      existing.transactionCount += item.transaction_count;
      if (item.risk_score > existing.riskScore) {
        existing.riskScore = item.risk_score;
        existing.riskLevel = item.risk_level;
      }
      if (existing.status !== item.status) {
        existing.status = null;
      }
      continue;
    }

    const group: AlertGroup = {
      groupKey,
      affiliateId: item.affiliate_id,
      affiliateName: item.affiliate_name,
      detectedAt: item.detected_at,
      detectedAtLabel,
      items: [item],
      riskScore: item.risk_score,
      riskLevel: item.risk_level,
      status: item.status,
      estimatedDamage: item.reward_amount,
      transactionCount: item.transaction_count,
      outcomeSummary: item.outcome_type,
      patternSummary: item.pattern,
    };
    groups.push(group);
    groupMap.set(groupKey, group);
  }

  for (const group of groups) {
    group.outcomeSummary = summarizeOutcomes(group.items);
    group.patternSummary =
      group.items.length > 1
        ? `同時刻に ${group.items.length} 件のアラート`
        : group.items[0]?.pattern ?? group.patternSummary;
  }

  return groups;
}

export function AlertsScreen({ searchParams }: AlertsScreenProps) {
  const searchParamsKey = JSON.stringify(searchParams ?? {});
  const router = useRouter();
  const pathname = usePathname();
  const tableId = useId();
  const routeFilters = useMemo(
    () => buildInitialFilters(parseSearchParamsKey(searchParamsKey)),
    [searchParamsKey],
  );
  const [filters, setFilters] = useState<AlertFilters>(() => buildInitialFilters(searchParams));
  const [data, setData] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [submittingStatus, setSubmittingStatus] = useState<ReviewStatus | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<string[]>([]);
  const filtersRef = useRef(filters);
  const dataRef = useRef(data);

  useEffect(() => {
    filtersRef.current = filters;
  }, [filters]);

  useEffect(() => {
    dataRef.current = data;
  }, [data]);

  async function loadAlerts(nextFilters: AlertFilters) {
    setLoading(true);
    setError(null);
    try {
      const response = await getAlerts({
        status: nextFilters.status,
        startDate: nextFilters.startDate,
        endDate: nextFilters.endDate,
        sort: nextFilters.sort,
        page: nextFilters.page,
        pageSize: nextFilters.pageSize,
      });
      setData(response);
      setFilters({
        status: response.applied_filters.status as AlertFilterStatus,
        startDate: response.applied_filters.start_date ?? "",
        endDate: response.applied_filters.end_date ?? "",
        sort: response.applied_filters.sort,
        page: response.page,
        pageSize: response.page_size,
      });
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "アラート一覧の取得に失敗しました。";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (areFiltersEqual(routeFilters, filtersRef.current)) {
      if (dataRef.current === null) {
        void loadAlerts(routeFilters);
      }
      return;
    }
    setFilters(routeFilters);
    void loadAlerts(routeFilters);
  }, [routeFilters]);

  function setFilter<K extends keyof AlertFilters>(key: K, value: AlertFilters[K]) {
    setFilters((current) => ({
      ...current,
      [key]: value,
    }));
  }

  function toggleSelection(findingKey: string) {
    setSelectedKeys((current) =>
      current.includes(findingKey)
        ? current.filter((value) => value !== findingKey)
        : [...current, findingKey],
    );
  }

  function toggleSelectAll(items: AlertListItem[]) {
    if (selectedKeys.length === items.length) {
      setSelectedKeys([]);
      return;
    }
    setSelectedKeys(items.map((item) => item.finding_key));
  }

  function toggleGroup(groupKey: string) {
    setExpandedGroups((current) =>
      current.includes(groupKey) ? current.filter((value) => value !== groupKey) : [...current, groupKey],
    );
  }

  function toggleGroupSelection(group: AlertGroup) {
    const groupKeys = group.items.map((item) => item.finding_key);
    const allSelected = groupKeys.every((key) => selectedKeys.includes(key));

    setSelectedKeys((current) => {
      if (allSelected) {
        return current.filter((key) => !groupKeys.includes(key));
      }
      return Array.from(new Set([...current, ...groupKeys]));
    });
  }

  async function handleBulkAction(status: ReviewStatus) {
    if (selectedKeys.length === 0) {
      return;
    }

    setSubmittingStatus(status);
    setError(null);
    try {
      const result = await reviewAlerts(selectedKeys, status);
      setSelectedKeys([]);
      await loadAlerts(filters);
      setFeedback(`${result.updated_count}件を更新しました。`);
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "アラート更新に失敗しました。";
      setError(message);
    } finally {
      setSubmittingStatus(null);
    }
  }

  const items = data?.items ?? [];
  const groups = buildAlertGroups(items);
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / filters.pageSize));

  async function handleSearch() {
    await loadAlerts({
      ...filters,
      page: 1,
    });
  }

  async function handlePageChange(nextPage: number) {
    await loadAlerts({
      ...filters,
      page: nextPage,
    });
  }

  useEffect(() => {
    const nextQuery = toFilterQuery(filters);
    const currentQuery = toFilterQuery(routeFilters);
    if (nextQuery === currentQuery) {
      return;
    }
    router.replace(`${pathname}?${nextQuery}`, { scroll: false });
  }, [filters, pathname, routeFilters, router]);

  return (
    <div className="screen-page">
      <PageHeader title="アラート一覧" description="" />

      {/* フィルターバー */}
      <div className="control-bar">
        <div className="form-field">
          <label htmlFor="alert-status">ステータス</label>
          <select
            id="alert-status"
            value={filters.status}
            onChange={(event) => setFilter("status", event.target.value as AlertFilterStatus)}
          >
            <option value="unhandled">未対応</option>
            <option value="investigating">調査中</option>
            <option value="confirmed_fraud">確定不正</option>
            <option value="white">ホワイト</option>
            <option value="all">すべて</option>
          </select>
        </div>

        <div className="form-field">
          <label htmlFor="alert-start-date">開始日</label>
          <input
            id="alert-start-date"
            type="date"
            value={filters.startDate}
            onChange={(event) => setFilter("startDate", event.target.value)}
          />
        </div>

        <div className="form-field">
          <label htmlFor="alert-end-date">終了日</label>
          <input
            id="alert-end-date"
            type="date"
            value={filters.endDate}
            onChange={(event) => setFilter("endDate", event.target.value)}
          />
        </div>

        <ActionButton onClick={() => void handleSearch()} disabled={loading}>
          絞り込む
        </ActionButton>
      </div>

      {data ? <StatusCountStrip counts={data.status_counts} /> : null}

      {feedback ? <div className="success-message">{feedback}</div> : null}
      {error && !data ? <ErrorState message={error} /> : null}

      {/* 選択時アクションバー */}
      {selectedKeys.length > 0 ? (
        <div className="selection-bar">
          <span className="selection-bar-count">{selectedKeys.length}件を選択中</span>
          <div className="selection-bar-actions">
            <ActionButton
              tone="danger"
              disabled={submittingStatus !== null}
              onClick={() => void handleBulkAction("confirmed_fraud")}
            >
              確定不正
            </ActionButton>
            <ActionButton
              disabled={submittingStatus !== null}
              onClick={() => void handleBulkAction("white")}
            >
              ホワイト
            </ActionButton>
            <ActionButton
              tone="warning"
              disabled={submittingStatus !== null}
              onClick={() => void handleBulkAction("investigating")}
            >
              調査中
            </ActionButton>
          </div>
        </div>
      ) : null}

      {loading && !data ? <LoadingState /> : null}

      {/* テーブル */}
      <div className="table-scroll-container" style={{ maxHeight: "calc(100vh - 300px)" }}>
        {error && data ? <ErrorState message={error} /> : null}
        {loading && data ? <LoadingState message="一覧を更新しています..." /> : null}
        {!loading && items.length === 0 ? (
          <EmptyState message="対象のアラートはありません。" />
        ) : (
          <table aria-label="フラウドアラート一覧" className="table-sticky-head">
            <thead>
              <tr>
                <th>
                  <SelectionCheckbox
                    ariaLabel="すべて選択"
                    checked={items.length > 0 && selectedKeys.length === items.length}
                    indeterminate={selectedKeys.length > 0 && selectedKeys.length < items.length}
                    onChange={() => toggleSelectAll(items)}
                  />
                </th>
                <th>リスク</th>
                <th>アフィリエイトID / 名称</th>
                <th>ステータス</th>
                <th>成果種別</th>
                <th>被害推定額</th>
                <th>検知日時</th>
              </tr>
            </thead>
            {groups.map((group, index) => {
              const detailsId = `${tableId}-group-${index}`;
                const groupKeys = group.items.map((item) => item.finding_key);
                const selectedCount = groupKeys.filter((key) => selectedKeys.includes(key)).length;
                const allSelected = groupKeys.length > 0 && selectedCount === groupKeys.length;
                const isGrouped = group.items.length > 1;
                const isExpanded = expandedGroups.includes(group.groupKey);

                return (
                  <tbody key={group.groupKey} id={isGrouped ? detailsId : undefined}>
                    <tr className={isGrouped ? "alert-group-summary" : undefined}>
                      <td>
                        <div className="alert-row-controls">
                          <SelectionCheckbox
                            ariaLabel={`${group.affiliateName} を選択`}
                            checked={allSelected}
                            indeterminate={!allSelected && selectedCount > 0}
                            onChange={() => (isGrouped ? toggleGroupSelection(group) : toggleSelection(groupKeys[0]))}
                          />
                          {isGrouped ? (
                            <button
                              className="table-toggle"
                              type="button"
                              aria-expanded={isExpanded}
                              aria-controls={detailsId}
                              onClick={() => toggleGroup(group.groupKey)}
                            >
                              {isExpanded ? "折りたたむ" : `${group.items.length}件を展開`}
                            </button>
                          ) : null}
                        </div>
                      </td>
                      <td>
                        <RiskBadge score={group.riskScore} level={group.riskLevel} />
                      </td>
                      <td>
                        {isGrouped ? (
                          <div className="table-link">
                            <span className="table-primary">{group.affiliateName}</span>
                            <span className="table-secondary">{group.affiliateId}</span>
                            <span className="table-tertiary">{group.patternSummary}</span>
                          </div>
                        ) : (
                          <Link className="table-link" href={`/alerts/${groupKeys[0]}`}>
                            <span className="table-primary">{group.affiliateName}</span>
                            <span className="table-secondary">{group.affiliateId}</span>
                          </Link>
                        )}
                      </td>
                      <td>
                        {group.status ? <StatusBadge status={group.status} /> : <span className="table-secondary">複数</span>}
                      </td>
                      <td>{group.outcomeSummary}</td>
                      <td>{formatCurrency(group.estimatedDamage)}</td>
                      <td>{group.detectedAtLabel}</td>
                    </tr>
                    {isGrouped && isExpanded
                      ? group.items.map((item) => (
                          <tr key={item.finding_key} className="alert-group-child">
                            <td>
                              <input
                                aria-label={`${item.affiliate_name} の個別アラートを選択`}
                                type="checkbox"
                                checked={selectedKeys.includes(item.finding_key)}
                                onChange={() => toggleSelection(item.finding_key)}
                              />
                            </td>
                            <td>
                              <RiskBadge score={item.risk_score} level={item.risk_level} />
                            </td>
                            <td>
                              <Link className="table-link" href={`/alerts/${item.finding_key}`}>
                                <span className="table-primary">{item.affiliate_name}</span>
                                <span className="table-secondary">{item.affiliate_id}</span>
                                <span className="table-tertiary">{item.pattern}</span>
                              </Link>
                            </td>
                            <td>
                              <StatusBadge status={item.status} />
                            </td>
                            <td>{item.outcome_type}</td>
                            <td>{formatCurrency(item.reward_amount)}</td>
                            <td>{formatDateTime(item.detected_at)}</td>
                          </tr>
                        ))
                      : null}
                  </tbody>
                );
              })}
          </table>
        )}
      </div>
      {data ? (
        <div className="control-bar" aria-label="pagination">
          <div className="table-secondary">
            {total}件中 {(filters.page - 1) * filters.pageSize + (items.length > 0 ? 1 : 0)}-
            {(filters.page - 1) * filters.pageSize + items.length}件を表示
          </div>
          <div className="selection-bar-actions">
            <ActionButton disabled={loading || filters.page <= 1} onClick={() => void handlePageChange(filters.page - 1)}>
              前へ
            </ActionButton>
            <span className="table-secondary">
              {filters.page} / {totalPages}
            </span>
            <ActionButton disabled={loading || !data.has_next} onClick={() => void handlePageChange(filters.page + 1)}>
              次へ
            </ActionButton>
          </div>
        </div>
      ) : null}
    </div>
  );
}
