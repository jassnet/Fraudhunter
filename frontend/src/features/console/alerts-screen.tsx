"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

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
    return "None";
  }
  if (items.length === 1) {
    return items[0]?.name ?? items[0]?.id ?? "None";
  }
  return `${items[0]?.name ?? items[0]?.id} +${items.length - 1}`;
}

function programPreview(item: AlertListItem) {
  if (item.affected_programs.length === 0) {
    return "None";
  }
  if (item.affected_programs.length === 1) {
    return item.affected_programs[0]?.name ?? item.affected_programs[0]?.id ?? "None";
  }
  return `${item.affected_programs[0]?.name ?? item.affected_programs[0]?.id} +${item.affected_programs.length - 1}`;
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
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus | null>(null);
  const [reviewReason, setReviewReason] = useState("");
  const [reviewReasonError, setReviewReasonError] = useState<string | null>(null);
  const { replace } = useRouter();
  const pathname = usePathname();

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
        const canonicalFilters = filtersFromResponse(response);
        if (toFilterQuery(filters) !== toFilterQuery(canonicalFilters)) {
          replace(`${pathname}?${toFilterQuery(canonicalFilters)}`, { scroll: false });
        }
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : "Failed to load alerts.");
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

  function setDraftFilter<K extends keyof AlertFilters>(key: K, value: AlertFilters[K]) {
    setDraftFilters((current) => ({ ...current, [key]: value }));
  }

  function replaceRoute(nextFilters: AlertFilters) {
    setFeedback(null);
    setWarning(null);
    replace(`${pathname}?${toFilterQuery(nextFilters)}`, { scroll: false });
  }

  function openBulkAction(status: ReviewStatus) {
    if (selectedKeys.length === 0) {
      return;
    }
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

  async function submitBulkAction() {
    if (reviewStatus === null || selectedKeys.length === 0) {
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
      const result = await reviewAlerts(selectedKeys, reviewStatus, reason);
      closeReviewDialog();
      setFeedback(`Updated ${result.updated_count} cases.`);
      setWarning(result.missing_keys.length > 0 ? `Missing cases: ${result.missing_keys.join(", ")}` : null);
      await loadAlerts(routeFilters);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Failed to update review.");
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
          <h1 className="alerts-title">Alerts</h1>
          {data ? <StatusCountStrip counts={data.status_counts} /> : null}
          <p className="table-secondary">Counts match the current filter scope.</p>
        </div>
        <div className="alerts-topbar-right">
          <a className="button button-default" href={exportUrl}>
            Export CSV
          </a>
        </div>
      </div>

      <div className="alerts-filters">
        <div className="alerts-filters-fields">
          <div className="form-field form-field--compact">
            <label htmlFor="alert-status">Status</label>
            <select
              id="alert-status"
              aria-label="Status"
              value={draftFilters.status}
              onChange={(event) => setDraftFilter("status", event.target.value as AlertFilterStatus)}
            >
              <option value="unhandled">Unhandled</option>
              <option value="investigating">Investigating</option>
              <option value="confirmed_fraud">Confirmed fraud</option>
              <option value="white">White</option>
              <option value="all">All</option>
            </select>
          </div>

          <div className="form-field form-field--compact">
            <label htmlFor="alert-risk-level">Risk level</label>
            <select
              id="alert-risk-level"
              aria-label="Risk level"
              value={draftFilters.riskLevel}
              onChange={(event) => setDraftFilter("riskLevel", event.target.value as AlertRiskFilter)}
            >
              <option value="all">All</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="form-field form-field--compact">
            <label htmlFor="alert-start-date">Start date</label>
            <input
              id="alert-start-date"
              aria-label="Start date"
              type="date"
              value={draftFilters.startDate}
              onChange={(event) => setDraftFilter("startDate", event.target.value)}
            />
          </div>

          <div className="form-field form-field--compact">
            <label htmlFor="alert-end-date">End date</label>
            <input
              id="alert-end-date"
              aria-label="End date"
              type="date"
              value={draftFilters.endDate}
              onChange={(event) => setDraftFilter("endDate", event.target.value)}
            />
          </div>

          <div className="form-field form-field--compact form-field--grow">
            <label htmlFor="alert-search">Search</label>
            <input
              id="alert-search"
              aria-label="Search"
              type="search"
              value={draftFilters.search}
              onChange={(event) => setDraftFilter("search", event.target.value)}
              placeholder="affiliate, IP, UA"
            />
          </div>

          <div className="alerts-filters-actions">
            <ActionButton onClick={() => replaceRoute({ ...draftFilters, page: 1 })} disabled={loading}>
              Apply
            </ActionButton>
            <ActionButton onClick={() => replaceRoute(DEFAULT_FILTERS)} disabled={loading}>
              Reset
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
          <span className="selection-bar-count">{selectedKeys.length} selected</span>
          <div className="selection-bar-actions">
            <ActionButton tone="danger" disabled={submittingStatus !== null} onClick={() => openBulkAction("confirmed_fraud")}>
              Mark fraud
            </ActionButton>
            <ActionButton disabled={submittingStatus !== null} onClick={() => openBulkAction("white")}>
              Mark white
            </ActionButton>
            <ActionButton tone="warning" disabled={submittingStatus !== null} onClick={() => openBulkAction("investigating")}>
              Mark investigating
            </ActionButton>
          </div>
        </div>
      ) : null}

      <ReviewReasonDialog
        open={reviewStatus !== null}
        title="Review reason"
        description="Add the reason for this bulk review before applying the status change."
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
        onConfirm={() => void submitBulkAction()}
        textareaProps={{
          autoFocus: true,
          rows: 5,
          maxLength: 500,
          placeholder: "Describe why this case status is changing.",
        }}
      />

      {loading && !data ? <LoadingState /> : null}

      <div className="alerts-table-area">
        {error && data ? <ErrorState message={error} /> : null}
        {loading && data ? <LoadingState message="Refreshing alerts..." /> : null}
        {!loading && items.length === 0 ? (
          <EmptyState message={activeFilters.search ? "No alerts match the current filters." : "No alerts found."} />
        ) : (
          <table aria-label="Fraud alerts" className="table-sticky-head">
            <thead>
              <tr>
                <th>
                  <input
                    aria-label="Select all alerts"
                    type="checkbox"
                    checked={allSelected}
                    onChange={() => setSelectedKeys(allSelected ? [] : items.map((item) => item.case_key))}
                  />
                </th>
                <th>Risk</th>
                <th>Affected affiliates</th>
                <th>Environment</th>
                <th>Status</th>
                <th>Damage</th>
                <th>Detected</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.case_key}>
                  <td>
                    <input
                      aria-label={`Select ${namedPreview(item.affected_affiliates)}`}
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
                      <span className="table-secondary">{`${item.affected_affiliate_count} affiliates / ${programPreview(item)}`}</span>
                      <span className="table-tertiary">{item.primary_reason}</span>
                    </Link>
                  </td>
                  <td>
                    <div className="table-link">
                      <span className="table-primary">{item.environment.ipaddress ?? "No IP"}</span>
                      <span className="table-secondary">{item.environment.useragent ?? "No user agent"}</span>
                      <span className="table-tertiary">{item.environment.date ?? "No date"}</span>
                    </div>
                  </td>
                  <td>
                    <StatusBadge status={item.status} />
                  </td>
                  <td>
                    <div className="amount-cell">
                      <span>{formatCurrency(item.reward_amount)}</span>
                      <span className={`meta-badge ${item.reward_amount_is_estimated ? "meta-badge-warning" : "meta-badge-muted"}`}>
                        {item.reward_amount_is_estimated ? "Estimated" : "Observed"}
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
            {total} total, showing {(activeFilters.page - 1) * activeFilters.pageSize + (items.length > 0 ? 1 : 0)}-
            {(activeFilters.page - 1) * activeFilters.pageSize + items.length}
          </span>
          <div className="selection-bar-actions">
            <ActionButton
              disabled={loading || activeFilters.page <= 1}
              onClick={() => replaceRoute({ ...activeFilters, page: activeFilters.page - 1 })}
            >
              Previous
            </ActionButton>
            <span className="table-secondary">
              {activeFilters.page} / {totalPages}
            </span>
            <ActionButton
              disabled={loading || !data.has_next}
              onClick={() => replaceRoute({ ...activeFilters, page: activeFilters.page + 1 })}
            >
              Next
            </ActionButton>
          </div>
        </div>
      ) : null}
    </div>
  );
}
