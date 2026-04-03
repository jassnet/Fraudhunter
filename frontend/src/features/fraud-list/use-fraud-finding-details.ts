"use client";

import { useCallback, useState } from "react";
import { fraudCopy } from "@/features/fraud-list/copy";
import type { FraudFindingItem } from "@/lib/api";
import { fetchFraudFindingDetail, toResourceIssue } from "@/lib/api";

export type FraudFindingDetailStatus = "idle" | "loading" | "ready" | "error";

export function useFraudFindingDetails() {
  const [selected, setSelected] = useState<FraudFindingItem | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<FraudFindingItem | null>(null);
  const [status, setStatus] = useState<FraudFindingDetailStatus>("idle");
  const [message, setMessage] = useState<string | null>(null);

  const openDetail = useCallback(async (item: FraudFindingItem) => {
    setSelected(item);
    setSelectedDetail(null);
    setStatus("loading");
    setMessage(null);

    if (!item.finding_key) {
      setSelectedDetail(item);
      setStatus("ready");
      return;
    }

    try {
      const detail = await fetchFraudFindingDetail(item.finding_key);
      setSelectedDetail(detail);
      setStatus("ready");
    } catch (error) {
      const issue = toResourceIssue(error, fraudCopy.states.detailError);
      setSelectedDetail(item);
      setStatus("error");
      setMessage(issue.message);
    }
  }, []);

  return {
    selectedItem: selectedDetail || selected,
    detailStatus: status,
    detailMessage: message,
    openDetail,
  };
}

