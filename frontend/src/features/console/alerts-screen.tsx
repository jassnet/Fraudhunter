"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

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

export function AlertsScreen() {
  const [filters, setFilters] = useState<AlertFilters>(DEFAULT_FILTERS);
  const [data, setData] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [submittingStatus, setSubmittingStatus] = useState<ReviewStatus | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

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
                <th>報酬額</th>
                <th>検知日時</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.finding_key}>
                  <td>
                    <input
                      aria-label={`${item.affiliate_name} を選択`}
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
                      <span className="table-primary">{item.affiliate_id}</span>
                      <span className="table-secondary">{item.affiliate_name}</span>
                    </Link>
                  </td>
                  <td>
                    <StatusBadge status={item.status} />
                  </td>
                  <td>{item.outcome_type}</td>
                  <td>{formatCurrency(item.reward_amount)}</td>
                  <td>{formatDateTime(item.detected_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
