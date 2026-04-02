"use client";

import { useEffect, useMemo, useState } from "react";
import { DateQuickSelect } from "@/components/date-quick-select";
import { LastUpdated } from "@/components/last-updated";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { StatePanel } from "@/components/ui/state-panel";
import {
  buildSuspiciousListQueryString,
  parseSuspiciousListUrlState,
  type SuspiciousRiskFilter,
  type SuspiciousSortValue,
} from "@/features/suspicious-list/url-state";
import {
  fetchFraudFindingDetail,
  fetchFraudFindings,
  getAvailableDates,
  getErrorMessage,
  type FraudFindingItem,
} from "@/lib/api";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

const PAGE_SIZE = 20;

function reasonSummary(item: FraudFindingItem) {
  return item.reason_summary?.trim() || item.reasons_formatted?.[0] || item.reasons?.[0] || "-";
}

export default function FraudListPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const state = useMemo(() => parseSuspiciousListUrlState(searchParams), [searchParams]);

  const [data, setData] = useState<FraudFindingItem[]>([]);
  const [total, setTotal] = useState(0);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "empty" | "error">("loading");
  const [message, setMessage] = useState<string | null>(null);
  const [searchDraft, setSearchDraft] = useState(state.search);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [selected, setSelected] = useState<FraudFindingItem | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<FraudFindingItem | null>(null);

  const replaceState = (patch: Partial<typeof state>) => {
    const next = { ...state, ...patch };
    const query = buildSuspiciousListQueryString(next);
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchDraft !== state.search) {
        replaceState({ search: searchDraft, page: 1 });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchDraft, state.search]);

  useEffect(() => {
    getAvailableDates()
      .then((result) => setAvailableDates(result.dates || []))
      .catch((error) => {
        setStatus("error");
        setMessage(getErrorMessage(error, "日付一覧の取得に失敗しました"));
      });
  }, []);

  useEffect(() => {
    if (!state.date && availableDates[0]) {
      replaceState({ date: availableDates[0], page: 1 });
    }
  }, [availableDates, state.date]);

  const load = async () => {
    if (!state.date) return;
    setStatus("loading");
    setMessage(null);
    try {
      const response = await fetchFraudFindings(state.date, PAGE_SIZE, (state.page - 1) * PAGE_SIZE, {
        search: state.search.trim() || undefined,
        riskLevel: state.risk === "all" ? undefined : state.risk,
        sortBy: state.sort,
        sortOrder: state.sortOrder,
      });
      setData(response.data || []);
      setTotal(response.total || 0);
      setLastUpdated(new Date());
      setStatus((response.total || 0) > 0 ? "ready" : "empty");
    } catch (error) {
      setStatus("error");
      setMessage(getErrorMessage(error, "不正判定一覧の取得に失敗しました"));
    }
  };

  useEffect(() => {
    void load();
  }, [state.date, state.page, state.risk, state.sort, state.sortOrder, state.search]);

  const openDetail = async (item: FraudFindingItem) => {
    setSelected(item);
    try {
      const detail = await fetchFraudFindingDetail(item.finding_key || "");
      setSelectedDetail(detail);
    } catch {
      setSelectedDetail(item);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <PageHeader
        className="shrink-0"
        title="不正判定"
        meta={state.date ? `対象日: ${state.date}` : "対象日を選択してください"}
        actions={
          <>
            <DateQuickSelect
              value={state.date}
              onChange={(value) => replaceState({ date: value, page: 1 })}
              availableDates={availableDates}
              showQuickButtons={false}
              className="gap-1.5"
            />
            <LastUpdated lastUpdated={lastUpdated} onRefresh={load} compact />
          </>
        }
      />

      <div className="border-b border-border bg-muted/20 px-3 py-2.5 sm:px-4">
        <div className="flex flex-wrap gap-2">
          <Input
            type="search"
            aria-label="検索"
            placeholder="アフィリエイター / メディア / 案件 / 理由で検索"
            value={searchDraft}
            onChange={(event) => setSearchDraft(event.target.value)}
            className="h-9 max-w-xl"
          />
          <select
            className="h-9 rounded-md border border-input bg-background px-2 text-sm"
            value={state.risk}
            onChange={(event) => replaceState({ risk: event.target.value as SuspiciousRiskFilter, page: 1 })}
          >
            <option value="all">すべて</option>
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
          </select>
          <select
            className="h-9 rounded-md border border-input bg-background px-2 text-sm"
            value={state.sort}
            onChange={(event) => replaceState({ sort: event.target.value as SuspiciousSortValue, page: 1 })}
          >
            <option value="count">件数順</option>
            <option value="risk">リスク順</option>
            <option value="latest">新しい順</option>
          </select>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 overflow-hidden">
        <div className="min-h-0 flex-1 overflow-auto p-4">
          {status === "error" ? (
            <StatePanel title="不正判定一覧の取得に失敗しました" message={message || undefined} tone="warning" />
          ) : status === "empty" ? (
            <StatePanel title="不正判定はありません" message="この日の findings は 0 件です。" tone="neutral" />
          ) : (
            <div className="space-y-3">
              <div className="text-sm text-foreground/80">
                {(total === 0 ? 0 : (state.page - 1) * PAGE_SIZE + 1).toLocaleString("ja-JP")} -
                {Math.min(state.page * PAGE_SIZE, total).toLocaleString("ja-JP")} / {total.toLocaleString("ja-JP")} 件
              </div>
              <div className="overflow-hidden rounded-lg border border-border">
                <table className="w-full table-fixed">
                  <thead className="bg-muted/40 text-left text-xs text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2">件数</th>
                      <th className="px-3 py-2">アフィリエイター</th>
                      <th className="px-3 py-2">メディア</th>
                      <th className="px-3 py-2">案件</th>
                      <th className="px-3 py-2">リスク</th>
                      <th className="px-3 py-2">理由</th>
                      <th className="px-3 py-2 text-right">詳細</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.map((item) => (
                      <tr key={item.finding_key} className="border-t border-border text-sm">
                        <td className="px-3 py-2 tabular-nums">{item.primary_metric.toLocaleString("ja-JP")}</td>
                        <td className="px-3 py-2">{item.user_name}</td>
                        <td className="px-3 py-2">{item.media_name}</td>
                        <td className="px-3 py-2">{item.promotion_name}</td>
                        <td className="px-3 py-2">{item.risk_label || item.risk_level || "-"}</td>
                        <td className="px-3 py-2">{reasonSummary(item)}</td>
                        <td className="px-3 py-2 text-right">
                          <Button size="sm" variant="outline" onClick={() => void openDetail(item)}>
                            詳細
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-sm text-foreground/70">
                  {state.page} / {totalPages}
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" disabled={state.page <= 1} onClick={() => replaceState({ page: 1 })}>
                    最初
                  </Button>
                  <Button size="sm" variant="outline" disabled={state.page <= 1} onClick={() => replaceState({ page: Math.max(1, state.page - 1) })}>
                    前へ
                  </Button>
                  <Button size="sm" variant="outline" disabled={state.page >= totalPages} onClick={() => replaceState({ page: Math.min(totalPages, state.page + 1) })}>
                    次へ
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        <aside className="hidden w-[28rem] shrink-0 border-l border-border bg-card p-4 lg:block">
          {selected ? (
            <div className="space-y-3 text-sm">
              <div>
                <div className="text-xs text-muted-foreground">アフィリエイター</div>
                <div>{(selectedDetail || selected).user_name}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">メディア</div>
                <div>{(selectedDetail || selected).media_name}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">案件</div>
                <div>{(selectedDetail || selected).promotion_name}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">理由</div>
                <ul className="list-disc pl-5">
                  {(selectedDetail || selected).reasons_formatted.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">メトリクス</div>
                <pre className="overflow-auto rounded border border-border bg-muted/30 p-3 text-xs">
                  {JSON.stringify((selectedDetail || selected).details || {}, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">一覧から詳細を選択してください。</div>
          )}
        </aside>
      </div>
    </div>
  );
}
