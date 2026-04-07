"use client";

import { Fragment, useEffect, useState } from "react";
import Link from "next/link";

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
};

const DEFAULT_FILTERS: AlertFilters = {
  status: "unhandled",
  startDate: "",
  endDate: "",
  sort: "risk_desc",
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

export function AlertsScreen() {
  const [filters, setFilters] = useState<AlertFilters>(DEFAULT_FILTERS);
  const [data, setData] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [submittingStatus, setSubmittingStatus] = useState<ReviewStatus | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<string[]>([]);

  async function loadAlerts(nextFilters: AlertFilters) {
    setLoading(true);
    setError(null);
    try {
      const response = await getAlerts({
        status: nextFilters.status,
        startDate: nextFilters.startDate,
        endDate: nextFilters.endDate,
        sort: nextFilters.sort,
      });
      setData(response);
      setFilters({
        status: response.applied_filters.status as AlertFilterStatus,
        startDate: response.applied_filters.start_date ?? "",
        endDate: response.applied_filters.end_date ?? "",
        sort: response.applied_filters.sort,
      });
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "アラート一覧の取得に失敗しました。";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAlerts(DEFAULT_FILTERS);
  }, []);

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

        <ActionButton onClick={() => void loadAlerts(filters)} disabled={loading}>
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
                  <input
                    aria-label="すべて選択"
                    type="checkbox"
                    checked={items.length > 0 && selectedKeys.length === items.length}
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
            <tbody>
              {groups.map((group) => {
                const groupKeys = group.items.map((item) => item.finding_key);
                const allSelected = groupKeys.every((key) => selectedKeys.includes(key));
                const isGrouped = group.items.length > 1;
                const isExpanded = expandedGroups.includes(group.groupKey);

                return (
                  <Fragment key={group.groupKey}>
                    <tr className={isGrouped ? "alert-group-summary" : undefined}>
                      <td>
                        <div className="alert-row-controls">
                          <input
                            aria-label={`${group.affiliateName} を選択`}
                            type="checkbox"
                            checked={allSelected}
                            onChange={() => (isGrouped ? toggleGroupSelection(group) : toggleSelection(groupKeys[0]))}
                          />
                          {isGrouped ? (
                            <button
                              className="table-toggle"
                              type="button"
                              aria-expanded={isExpanded}
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
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
