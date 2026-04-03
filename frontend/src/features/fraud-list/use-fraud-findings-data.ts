"use client";

import { useCallback, useEffect, useEffectEvent, useMemo, useState } from "react";
import { fraudCopy } from "@/features/fraud-list/copy";
import { FRAUD_FINDINGS_PAGE_SIZE } from "@/features/fraud-list/fraud-findings-content";
import type { SuspiciousDataStatus } from "@/features/suspicious-list/use-suspicious-data";
import type {
  SuspiciousRiskFilter,
  SuspiciousSortOrder,
  SuspiciousSortValue,
} from "@/features/suspicious-list/url-state";
import {
  fetchFraudFindings,
  getAvailableDates,
  toResourceIssue,
  type FraudFindingItem,
  type FraudFindingsResponse,
} from "@/lib/api";

interface UseFraudFindingsDataArgs {
  date: string;
  page: number;
  risk: SuspiciousRiskFilter;
  search: string;
  sort: SuspiciousSortValue;
  sortOrder: SuspiciousSortOrder;
}

function getResultRange(page: number, total: number, visibleCount: number, status: SuspiciousDataStatus) {
  if (status === "loading" || status === "refreshing") {
    return fraudCopy.states.loadingRange;
  }

  if (total === 0) {
    return fraudCopy.states.emptyRange;
  }

  const start = (page - 1) * FRAUD_FINDINGS_PAGE_SIZE + 1;
  const end = Math.min(start + visibleCount - 1, total);
  return fraudCopy.formatResultRange(start, end, total);
}

export function useFraudFindingsData({
  date,
  page,
  risk,
  search,
  sort,
  sortOrder,
}: UseFraudFindingsDataArgs) {
  const [data, setData] = useState<FraudFindingItem[]>([]);
  const [total, setTotal] = useState(0);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [visibleCount, setVisibleCount] = useState(0);
  const [status, setStatus] = useState<SuspiciousDataStatus>("loading");
  const [message, setMessage] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [resolvedDate, setResolvedDate] = useState("");

  const executeLoadData = useCallback(async (refresh = false) => {
    setStatus(refresh ? "refreshing" : "loading");
    setMessage(null);

    try {
      const response: FraudFindingsResponse = await fetchFraudFindings(
        date || undefined,
        FRAUD_FINDINGS_PAGE_SIZE,
        (page - 1) * FRAUD_FINDINGS_PAGE_SIZE,
        {
          search: search.trim() || undefined,
          riskLevel: risk === "all" ? undefined : risk,
          sortBy: sort,
          sortOrder,
        }
      );

      setData(response.data || []);
      setTotal(response.total || 0);
      setVisibleCount((response.data || []).length);
      setResolvedDate(response.date || "");
      if (response.date) {
        setAvailableDates((current) =>
          current.includes(response.date) ? current : [response.date, ...current]
        );
      }
      setLastUpdated(new Date());
      setStatus((response.total || 0) > 0 ? "ready" : "empty");
    } catch (error) {
      const issue = toResourceIssue(error, fraudCopy.states.loadErrorMessage);
      setMessage(issue.message);
      setStatus(issue.kind);
    }
  }, [date, page, risk, search, sort, sortOrder]);

  useEffect(() => {
    const loadDates = async () => {
      try {
        const result = await getAvailableDates();
        setAvailableDates(result.dates || []);
      } catch (error) {
        const issue = toResourceIssue(error, fraudCopy.states.datesErrorMessage);
        setStatus(issue.kind);
        setMessage(issue.message);
      }
    };

    void loadDates();
  }, []);

  const loadData = useEffectEvent(async () => {
    await executeLoadData(false);
  });

  useEffect(() => {
    void loadData();
  }, [date, page, risk, search, sort, sortOrder]);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / FRAUD_FINDINGS_PAGE_SIZE)), [total]);
  const resultRange = useMemo(
    () => getResultRange(page, total, visibleCount, status),
    [page, total, visibleCount, status]
  );

  return {
    data,
    availableDates,
    status,
    message,
    lastUpdated,
    resolvedDate,
    totalPages,
    resultRange,
    reload: () => void executeLoadData(true),
  };
}
