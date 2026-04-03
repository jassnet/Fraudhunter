"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const GROUP_BY_REASON_STORAGE_KEY = "suspicious:list:group-by-reason:v2";

function readGroupByReasonPreference() {
  if (typeof window === "undefined") {
    return false;
  }

  try {
    const stored = window.localStorage.getItem(GROUP_BY_REASON_STORAGE_KEY);
    return stored === "1";
  } catch {
    return false;
  }
}

interface UseSuspiciousListDisplayStateArgs {
  page: number;
  search: string;
  onPageChange: (page: number) => void;
  onSearchCommit: (search: string) => void;
}

export function useSuspiciousListDisplayState({
  page,
  search,
  onPageChange,
  onSearchCommit,
}: UseSuspiciousListDisplayStateArgs) {
  const [groupByReason, setGroupByReason] = useState(readGroupByReasonPreference);
  const [searchDraft, setSearchDraft] = useState(search);
  const [searchPanelOpen, setSearchPanelOpen] = useState(() => search.trim().length > 0);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!searchPanelOpen) {
      return;
    }

    const animationFrameId = requestAnimationFrame(() => {
      searchInputRef.current?.focus();
    });

    return () => cancelAnimationFrame(animationFrameId);
  }, [searchPanelOpen]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      if (searchDraft !== search) {
        onSearchCommit(searchDraft);
      }
    }, 300);

    return () => window.clearTimeout(timeoutId);
  }, [onSearchCommit, search, searchDraft]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    try {
      window.localStorage.setItem(GROUP_BY_REASON_STORAGE_KEY, groupByReason ? "1" : "0");
    } catch {
      // ignore storage failures
    }
  }, [groupByReason]);

  const handleGroupByReasonChange = useCallback(
    (checked: boolean) => {
      setGroupByReason(checked);
      if (page !== 1) {
        onPageChange(1);
      }
    },
    [onPageChange, page]
  );

  return {
    groupByReason,
    searchDraft,
    searchInputRef,
    searchPanelOpen,
    setSearchDraft,
    setSearchPanelOpen,
    handleGroupByReasonChange,
  };
}
