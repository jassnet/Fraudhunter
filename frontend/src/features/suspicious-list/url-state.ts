"use client";

import { useCallback, useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

export type SuspiciousRiskFilter = "all" | "high" | "medium" | "low";
export type SuspiciousSortValue = "count" | "risk" | "latest";
export type SuspiciousSortOrder = "asc" | "desc";
type SearchParamsLike = Pick<URLSearchParams, "get">;

export interface SuspiciousListUrlState {
  date: string;
  page: number;
  search: string;
  risk: SuspiciousRiskFilter;
  sort: SuspiciousSortValue;
  sortOrder: SuspiciousSortOrder;
}

export function parsePageValue(value: string | null): number {
  if (!value) return 1;
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 1;
}

export function parseRiskFilter(value: string | null): SuspiciousRiskFilter {
  return value === "high" || value === "medium" || value === "low" ? value : "all";
}

export function parseSortValue(value: string | null): SuspiciousSortValue {
  return value === "risk" || value === "latest" ? value : "count";
}

export function parseSortOrder(value: string | null): SuspiciousSortOrder {
  return value === "asc" ? "asc" : "desc";
}

export function parseSuspiciousListUrlState(
  searchParams: SearchParamsLike
): SuspiciousListUrlState {
  return {
    date: searchParams.get("date") || "",
    page: parsePageValue(searchParams.get("page")),
    search: searchParams.get("search") || "",
    risk: parseRiskFilter(searchParams.get("risk")),
    sort: parseSortValue(searchParams.get("sort")),
    sortOrder: parseSortOrder(searchParams.get("sort_order")),
  };
}

export function buildSuspiciousListQueryString(state: SuspiciousListUrlState): string {
  const params = new URLSearchParams();
  if (state.date) params.set("date", state.date);
  if (state.search.trim()) params.set("search", state.search.trim());
  if (state.page > 1) params.set("page", String(state.page));
  if (state.risk !== "all") params.set("risk", state.risk);
  if (state.sort !== "count") params.set("sort", state.sort);
  if (state.sortOrder !== "desc") params.set("sort_order", state.sortOrder);
  return params.toString();
}

export function useSuspiciousListUrlState() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const state = useMemo(
    () => parseSuspiciousListUrlState(searchParams),
    [searchParams]
  );

  const replaceState = useCallback(
    (patch: Partial<SuspiciousListUrlState>) => {
      const nextState: SuspiciousListUrlState = {
        ...state,
        ...patch,
      };
      const query = buildSuspiciousListQueryString(nextState);
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [pathname, router, state]
  );

  return {
    state,
    replaceState,
    setDate: (date: string) => replaceState({ date, page: 1 }),
    setPage: (page: number) => replaceState({ page }),
    setSearch: (search: string) => replaceState({ search, page: 1 }),
    setRisk: (risk: SuspiciousRiskFilter) => replaceState({ risk, page: 1 }),
    setSort: (sort: SuspiciousSortValue, sortOrder: SuspiciousSortOrder = "desc") =>
      replaceState({ sort, sortOrder, page: 1 }),
  };
}
