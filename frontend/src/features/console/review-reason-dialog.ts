"use client";

import { useEffect, useState } from "react";

import type { ReviewStatus } from "@/lib/console-types";

type UseReviewReasonDialogResult = {
  reviewStatus: ReviewStatus | null;
  reviewReason: string;
  reviewReasonError: string | null;
  openReviewDialog: (status: ReviewStatus) => void;
  closeReviewDialog: () => void;
  setReviewReasonValue: (value: string) => void;
  validateReviewReason: () => string | null;
  clearReviewReasonError: () => void;
};

function resetReasonState(
  setReviewStatus: (status: ReviewStatus | null) => void,
  setReviewReason: (reason: string) => void,
  setReviewReasonError: (error: string | null) => void,
) {
  setReviewStatus(null);
  setReviewReason("");
  setReviewReasonError(null);
}

export function reviewStatusActionLabel(status: ReviewStatus) {
  if (status === "confirmed_fraud") {
    return "この内容で不正確定";
  }
  if (status === "white") {
    return "この内容で正常確定";
  }
  return "この内容で調査中に変更";
}

export function reviewStatusConfirmTone(status: ReviewStatus): "danger" | "warning" | "default" {
  if (status === "confirmed_fraud") {
    return "danger";
  }
  if (status === "investigating") {
    return "warning";
  }
  return "default";
}

export function reviewReasonPresets(status: ReviewStatus): string[] {
  if (status === "confirmed_fraud") {
    return [
      "同一環境から短時間に成果が集中しており、不正の疑いが高いです。",
      "クリックから成果までの時間が不自然に短く、自動化の疑いがあります。",
      "複数案件にまたがる同一環境の成果が確認され、支払保留が必要です。",
    ];
  }
  if (status === "white") {
    return [
      "実データを確認し、正常な成果と判断しました。",
      "検知理由を確認したが、業務上の妥当な範囲でした。",
    ];
  }
  return [
    "追加確認が必要なため継続調査します。",
    "関連案件と照合してから最終判定します。",
  ];
}

export function useReviewReasonDialog(isBusy: boolean): UseReviewReasonDialogResult {
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus | null>(null);
  const [reviewReason, setReviewReason] = useState("");
  const [reviewReasonError, setReviewReasonError] = useState<string | null>(null);

  useEffect(() => {
    if (reviewStatus === null) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isBusy) {
        resetReasonState(setReviewStatus, setReviewReason, setReviewReasonError);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isBusy, reviewStatus]);

  function openReviewDialog(status: ReviewStatus) {
    setReviewStatus(status);
    setReviewReason("");
    setReviewReasonError(null);
  }

  function closeReviewDialog() {
    if (isBusy) {
      return;
    }
    resetReasonState(setReviewStatus, setReviewReason, setReviewReasonError);
  }

  function setReviewReasonValue(value: string) {
    setReviewReason(value);
    if (reviewReasonError) {
      setReviewReasonError(null);
    }
  }

  function validateReviewReason() {
    const trimmedReason = reviewReason.trim();
    if (!trimmedReason) {
      setReviewReasonError("判定の理由を入力してください。");
      return null;
    }
    return trimmedReason;
  }

  function clearReviewReasonError() {
    setReviewReasonError(null);
  }

  return {
    reviewStatus,
    reviewReason,
    reviewReasonError,
    openReviewDialog,
    closeReviewDialog,
    setReviewReasonValue,
    validateReviewReason,
    clearReviewReasonError,
  };
}
