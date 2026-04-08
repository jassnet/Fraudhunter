"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
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
import { buildAlertsCsvUrl, getAlerts, reviewAlerts } from "@/lib/console-api";
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
  search: string;
  sort: string;
  page: number;
  pageSize: number;
};

const DEFAULT_FILTERS: AlertFilters = {
  status: "unhandled",
  startDate: "",
  endDate: "",
  search: "",
  sort: "risk_desc",
  page: 1,
  pageSize: 50,
};

type AlertGroup = {
  groupKey: string;
  affiliateId: string;
  affiliateName: string;
  detectedAtLabel: string;
  items: AlertListItem[];
  riskScore: number;
  riskLevel: AlertListItem["risk_level"];
  status: ReviewStatus | null;
  estimatedDamage: number;
  rewardAmountIsEstimated: boolean;
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

function RewardAmountCell({
  amount,
  estimated,
}: {
  amount: number;
  estimated: boolean;
}) {
  return (
    <div className="amount-cell">
      <span>{formatCurrency(amount)}</span>
      <span className={`meta-badge ${estimated ? "meta-badge-warning" : "meta-badge-muted"}`}>
        {estimated ? "推定" : "実測"}
      </span>
    </div>
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
  const search = firstSearchParam(searchParams.search);
  const sort = firstSearchParam(searchParams.sort);
  const page = Number(firstSearchParam(searchParams.page) || DEFAULT_FILTERS.page);
  const pageSize = Number(firstSearchParam(searchParams.page_size) || DEFAULT_FILTERS.pageSize);

  return {
    status: (status || DEFAULT_FILTERS.status) as AlertFilterStatus,
    startDate,
    endDate,
    search,
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
  if (filters.search.trim()) {
    query.set("search", filters.search.trim());
  }
  return query.toString();
}

function filtersFromResponse(response: AlertsResponse): AlertFilters {
  return {
    status: response.applied_filters.status as AlertFilterStatus,
    startDate: response.applied_filters.start_date ?? "",
    endDate: response.applied_filters.end_date ?? "",
    search: response.applied_filters.search ?? "",
    sort: response.applied_filters.sort,
    page: response.page,
    pageSize: response.page_size,
  };
}

function summarizeOutcomes(items: AlertListItem[]) {
  const uniqueOutcomeTypes = Array.from(new Set(items.map((item) => item.outcome_type)));
  if (uniqueOutcomeTypes.length === 0) {
    return "不明";
  }
  if (uniqueOutcomeTypes.length <= 2) {
    return uniqueOutcomeTypes.join(" / ");
  }
  return `${uniqueOutcomeTypes.slice(0, 2).join(" / ")} ほか${uniqueOutcomeTypes.length - 2}件`;
}

function buildAlertGroups(items: AlertListItem[]) {
  const groups: AlertGroup[] = [];
  const groupMap = new Map<string, AlertGroup>();

  for (const item of items) {
    const groupKey = `${item.affiliate_id}::${item.detected_at}`;
    const existing = groupMap.get(groupKey);

    if (existing) {
      existing.items.push(item);
      existing.estimatedDamage += item.reward_amount;
      existing.rewardAmountIsEstimated = existing.rewardAmountIsEstimated || item.reward_amount_is_estimated;
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
      detectedAtLabel: formatDateTime(item.detected_at),
      items: [item],
      riskScore: item.risk_score,
      riskLevel: item.risk_level,
      status: item.status,
      estimatedDamage: item.reward_amount,
      rewardAmountIsEstimated: item.reward_amount_is_estimated,
      outcomeSummary: item.outcome_type,
      patternSummary: item.pattern,
    };
    groups.push(group);
    groupMap.set(groupKey, group);
  }

  for (const group of groups) {
    group.outcomeSummary = summarizeOutcomes(group.items);
    group.patternSummary =
      group.items.length > 1 ? `${group.items.length}件のアラートをまとめて表示` : group.items[0]?.pattern ?? "";
  }

  return groups;
}

export function AlertsScreen({ searchParams }: AlertsScreenProps) {
  const searchParamsKey = JSON.stringify(searchParams ?? {});
  const { replace } = useRouter();
  const pathname = usePathname();
  const tableId = useId();
  const routeFilters = useMemo(
    () => buildInitialFilters(parseSearchParamsKey(searchParamsKey)),
    [searchParamsKey],
  );
  const [draftFilters, setDraftFilters] = useState<AlertFilters>(() => buildInitialFilters(searchParams));
  const [data, setData] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [submittingStatus, setSubmittingStatus] = useState<ReviewStatus | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<string[]>([]);
  const latestRequestId = useRef(0);

  const loadAlerts = useCallback(async (nextFilters: AlertFilters) => {
    const requestId = latestRequestId.current + 1;
    latestRequestId.current = requestId;
    setLoading(true);
    setError(null);

    try {
      const response = await getAlerts({
        status: nextFilters.status,
        startDate: nextFilters.startDate,
        endDate: nextFilters.endDate,
        search: nextFilters.search,
        sort: nextFilters.sort,
        page: nextFilters.page,
        pageSize: nextFilters.pageSize,
      });
      if (latestRequestId.current !== requestId) {
        return;
      }

      setData(response);
      setSelectedKeys([]);
      setExpandedGroups([]);

      const canonicalFilters = filtersFromResponse(response);
      if (toFilterQuery(nextFilters) !== toFilterQuery(canonicalFilters)) {
        replace(`${pathname}?${toFilterQuery(canonicalFilters)}`, { scroll: false });
      }
    } catch (caughtError) {
      if (latestRequestId.current !== requestId) {
        return;
      }
      const message =
        caughtError instanceof Error ? caughtError.message : "アラート一覧の取得に失敗しました。";
      setError(message);
    } finally {
      if (latestRequestId.current === requestId) {
        setLoading(false);
      }
    }
  }, [pathname, replace]);

  useEffect(() => {
    setDraftFilters(routeFilters);
    void loadAlerts(routeFilters);
  }, [loadAlerts, routeFilters]);

  function setDraftFilter<K extends keyof AlertFilters>(key: K, value: AlertFilters[K]) {
    setDraftFilters((current) => ({
      ...current,
      [key]: value,
    }));
  }

  function replaceRoute(nextFilters: AlertFilters) {
    setFeedback(null);
    replace(`${pathname}?${toFilterQuery(nextFilters)}`, { scroll: false });
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
      setFeedback(`${result.updated_count}件のアラートを更新しました。`);
      await loadAlerts(routeFilters);
    } catch (caughtError) {
      const message =
        caughtError instanceof Error ? caughtError.message : "アラート更新に失敗しました。";
      setError(message);
    } finally {
      setSubmittingStatus(null);
    }
  }

  const items = data?.items ?? [];
  const groups = buildAlertGroups(items);
  const activeFilters = data ? filtersFromResponse(data) : routeFilters;
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / activeFilters.pageSize));
  const exportUrl = buildAlertsCsvUrl({
    status: activeFilters.status,
    startDate: activeFilters.startDate,
    endDate: activeFilters.endDate,
    search: activeFilters.search,
    sort: activeFilters.sort,
  });

  return (
    <div className="screen-page">
      <PageHeader
        title="アラート一覧"
        description="検索、日付、レビュー状態で絞り込みながら不正候補を確認します。"
        actions={
          <a className="button button-default" href={exportUrl}>
            CSVエクスポート
          </a>
        }
      />

      <div className="control-bar">
        <div className="controls-grid">
          <div className="form-field">
            <label htmlFor="alert-status">レビュー状態</label>
            <select
              id="alert-status"
              aria-label="レビュー状態"
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

          <div className="form-field">
            <label htmlFor="alert-search">検索</label>
            <input
              id="alert-search"
              aria-label="検索"
              type="search"
              value={draftFilters.search}
              onChange={(event) => setDraftFilter("search", event.target.value)}
              placeholder="アフィリエイトID、名称、パターン"
            />
          </div>

          <div className="form-field">
            <label htmlFor="alert-start-date">開始日</label>
            <input
              id="alert-start-date"
              aria-label="開始日"
              type="date"
              value={draftFilters.startDate}
              onChange={(event) => setDraftFilter("startDate", event.target.value)}
            />
          </div>

          <div className="form-field">
            <label htmlFor="alert-end-date">終了日</label>
            <input
              id="alert-end-date"
              aria-label="終了日"
              type="date"
              value={draftFilters.endDate}
              onChange={(event) => setDraftFilter("endDate", event.target.value)}
            />
          </div>
        </div>

        <div className="controls-actions">
          <ActionButton
            onClick={() =>
              replaceRoute({
                ...draftFilters,
                page: 1,
              })
            }
            disabled={loading}
          >
            絞り込む
          </ActionButton>
          <ActionButton onClick={() => replaceRoute(DEFAULT_FILTERS)} disabled={loading}>
            リセット
          </ActionButton>
        </div>
      </div>

      <div className="selection-summary">
        <span>対象期間: {activeFilters.startDate || "自動"} - {activeFilters.endDate || "自動"}</span>
        <span>検索語: {activeFilters.search || "なし"}</span>
      </div>

      {data ? <StatusCountStrip counts={data.status_counts} /> : null}
      {feedback ? <div className="success-message">{feedback}</div> : null}
      {error && !data ? <ErrorState message={error} /> : null}

      {selectedKeys.length > 0 ? (
        <div className="selection-bar">
          <span className="selection-bar-count">{selectedKeys.length}件を選択中</span>
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

      <div className="table-scroll-container" style={{ maxHeight: "calc(100vh - 320px)" }}>
        {error && data ? <ErrorState message={error} /> : null}
        {loading && data ? <LoadingState message="アラートを更新しています..." /> : null}
        {!loading && items.length === 0 ? (
          <EmptyState
            message={
              activeFilters.search
                ? "条件に一致するアラートはありません。"
                : "対象期間のアラートはありません。"
            }
          />
        ) : (
          <table aria-label="不正アラート一覧" className="table-sticky-head">
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
                <th>アフィリエイト / パターン</th>
                <th>レビュー状態</th>
                <th>成果</th>
                <th>想定報酬</th>
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
                            {isExpanded ? "折りたたむ" : `${group.items.length}件を表示`}
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
                          <Link className="table-tertiary" href={`/alerts/${groupKeys[0]}`}>
                            詳細を見る
                          </Link>
                        </div>
                      ) : (
                        <Link className="table-link" href={`/alerts/${groupKeys[0]}`}>
                          <span className="table-primary">{group.affiliateName}</span>
                          <span className="table-secondary">{group.affiliateId}</span>
                          <span className="table-tertiary">{group.patternSummary}</span>
                        </Link>
                      )}
                    </td>
                    <td>
                      {group.status ? <StatusBadge status={group.status} /> : <span className="table-secondary">混在</span>}
                    </td>
                    <td>{group.outcomeSummary}</td>
                    <td>
                      <RewardAmountCell amount={group.estimatedDamage} estimated={group.rewardAmountIsEstimated} />
                    </td>
                    <td>{group.detectedAtLabel}</td>
                  </tr>
                  {isGrouped && isExpanded
                    ? group.items.map((item) => (
                        <tr key={item.finding_key} className="alert-group-child">
                          <td>
                            <input
                              aria-label={`${item.affiliate_name} のアラートを選択`}
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
                          <td>
                            <RewardAmountCell
                              amount={item.reward_amount}
                              estimated={item.reward_amount_is_estimated}
                            />
                          </td>
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
            {total}件中 {(activeFilters.page - 1) * activeFilters.pageSize + (items.length > 0 ? 1 : 0)}-
            {(activeFilters.page - 1) * activeFilters.pageSize + items.length}件を表示
          </div>
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
