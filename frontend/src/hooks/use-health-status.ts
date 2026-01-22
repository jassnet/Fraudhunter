"use client";

import { useSyncExternalStore } from "react";
import { getHealthStatus, HealthIssue } from "@/lib/api";

type HealthStatus = "ok" | "warning" | "error" | "loading";

type Snapshot = {
  status: HealthStatus;
  issues: HealthIssue[];
};

let snapshot: Snapshot = { status: "loading", issues: [] };
const listeners = new Set<() => void>();
let pollTimer: ReturnType<typeof setTimeout> | null = null;
let inFlight = false;

const notify = () => {
  listeners.forEach((listener) => listener());
};

const scheduleNext = () => {
  pollTimer = setTimeout(poll, 30000);
};

const poll = async () => {
  if (inFlight) return;
  inFlight = true;
  try {
    const health = await getHealthStatus();
    snapshot = { status: health.status, issues: health.issues };
  } catch (error) {
    console.error("Health check failed", error);
    snapshot = {
      status: "error",
      issues: [
        {
          type: "error",
          field: "connection",
          message: "バックエンドに接続できません",
          hint: "バックエンドサーバーが起動しているか確認してください",
        },
      ],
    };
  } finally {
    inFlight = false;
    notify();
    if (listeners.size > 0) {
      scheduleNext();
    }
  }
};

const subscribe = (listener: () => void) => {
  listeners.add(listener);
  if (listeners.size === 1) {
    poll();
  }
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0 && pollTimer) {
      clearTimeout(pollTimer);
      pollTimer = null;
    }
  };
};

const getSnapshot = () => snapshot;

export function useHealthStatus() {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
