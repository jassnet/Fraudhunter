"use client";

import { useCallback, useState } from "react";
import type { SuspiciousItem } from "@/lib/api";
import { toResourceIssue } from "@/lib/api";

export type SuspiciousDetailStatus =
  | "idle"
  | "loading"
  | "ready"
  | "expired"
  | "unauthorized"
  | "forbidden"
  | "error";

type SuspiciousDetailFetcher = (findingKey: string) => Promise<SuspiciousItem>;

function withRecordValue<T>(current: Record<string, T>, key: string, value: T) {
  const next = { ...current };
  next[key] = value;
  return next;
}

export function useSuspiciousDetails(fetchDetail: SuspiciousDetailFetcher) {
  const [detailCache, setDetailCache] = useState<Record<string, SuspiciousItem>>({});
  const [detailStatusByKey, setDetailStatusByKey] = useState<
    Record<string, SuspiciousDetailStatus>
  >({});
  const [detailMessageByKey, setDetailMessageByKey] = useState<Record<string, string | null>>({});

  const loadDetail = useCallback(
    async (item: SuspiciousItem) => {
      const key = item.finding_key;
      if (!key) return;
      if (detailCache[key]?.details?.length) return;

      setDetailStatusByKey((current) => withRecordValue(current, key, "loading"));
      setDetailMessageByKey((current) => withRecordValue(current, key, null));

      try {
        const detailItem = await fetchDetail(key);
        setDetailCache((current) => withRecordValue(current, key, detailItem));
        setDetailStatusByKey((current) =>
          withRecordValue(
            current,
            key,
            detailItem.evidence_status === "expired" || detailItem.evidence_expired
              ? "expired"
              : "ready"
          )
        );
      } catch (error) {
        const issue = toResourceIssue(error, "詳細の取得に失敗しました。");
        const resolvedStatus: SuspiciousDetailStatus =
          issue.kind === "unauthorized"
            ? "unauthorized"
            : issue.kind === "forbidden"
              ? "forbidden"
              : "error";
        setDetailStatusByKey((current) => withRecordValue(current, key, resolvedStatus));
        setDetailMessageByKey((current) => withRecordValue(current, key, issue.message));
      }
    },
    [detailCache, fetchDetail]
  );

  const getDetailState = useCallback(
    (item: SuspiciousItem) => {
      const key = item.finding_key;
      if (!key) {
        return {
          item,
          status:
            item.evidence_status === "expired" || item.evidence_expired ? "expired" : "ready",
          message: null,
        } as const;
      }

      const resolved = detailCache[key] ? { ...item, ...detailCache[key] } : item;
      return {
        item: resolved,
        status:
          detailStatusByKey[key] ||
          (resolved.evidence_status === "expired" || resolved.evidence_expired
            ? "expired"
            : "idle"),
        message: detailMessageByKey[key] || null,
      } as const;
    },
    [detailCache, detailMessageByKey, detailStatusByKey]
  );

  return {
    loadDetail,
    getDetailState,
  };
}
