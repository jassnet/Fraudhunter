"use client";

import { useSyncExternalStore } from "react";
import { getJobStatus, JobStatusResponse } from "@/lib/api";

export type JobState = JobStatusResponse;

type Snapshot = {
  jobState: JobState | null;
  error: boolean;
};

let snapshot: Snapshot = { jobState: null, error: false };
const listeners = new Set<() => void>();
let pollTimer: ReturnType<typeof setTimeout> | null = null;
let inFlight = false;

const notify = () => {
  listeners.forEach((listener) => listener());
};

const scheduleNext = (state: JobState | null) => {
  const delay = state?.status === "running" ? 2000 : 10000;
  pollTimer = setTimeout(poll, delay);
};

const poll = async () => {
  if (inFlight) return;
  inFlight = true;
  try {
    const status = await getJobStatus();
    snapshot = { jobState: status, error: false };
  } catch (error) {
    console.error("Failed to fetch job status", error);
    snapshot = { jobState: snapshot.jobState, error: true };
  } finally {
    inFlight = false;
    notify();
    if (listeners.size > 0) {
      scheduleNext(snapshot.jobState);
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

export function useJobStatus() {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
