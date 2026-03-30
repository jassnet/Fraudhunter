export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export type RetryOptions = {
  retries?: number;
  retryDelayMs?: number;
  retryOn?: (status: number) => boolean;
};

export class ApiError extends Error {
  status?: number;
  detail?: string;
  payload?: unknown;
}

export type ResourceIssueKind =
  | "unauthorized"
  | "forbidden"
  | "transient-error"
  | "error";

export interface ResourceIssue {
  kind: ResourceIssueKind;
  message: string;
  retryable: boolean;
}

const DEFAULT_RETRY_DELAY_MS = 500;
const defaultRetryOn = (status: number) =>
  status === 408 || status === 429 || (status >= 500 && status <= 599);

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function fetchJson<T>(
  url: string,
  init?: RequestInit,
  options: RetryOptions = {}
): Promise<T> {
  const {
    retries = 2,
    retryDelayMs = DEFAULT_RETRY_DELAY_MS,
    retryOn = defaultRetryOn,
  } = options;
  let attempt = 0;

  while (true) {
    try {
      const res = await fetch(url, init);
      if (!res.ok) {
        let detail = "";
        let payload: unknown;
        try {
          payload = await res.json();
          if (typeof payload === "string") {
            detail = payload;
          } else if (
            typeof payload === "object" &&
            payload !== null &&
            "detail" in payload
          ) {
            detail =
              typeof payload.detail === "string"
                ? payload.detail
                : JSON.stringify(payload.detail);
          } else if (
            typeof payload === "object" &&
            payload !== null &&
            "message" in payload
          ) {
            detail = String(payload.message);
          }
        } catch {
          detail = "";
        }

        const error = new ApiError(detail || `Request failed (${res.status})`);
        error.status = res.status;
        error.detail = detail;
        error.payload = payload;

        if (attempt < retries && retryOn(res.status)) {
          attempt += 1;
          await sleep(retryDelayMs * attempt);
          continue;
        }
        throw error;
      }

      return res.json();
    } catch (error) {
      const isAbortError = error instanceof DOMException && error.name === "AbortError";
      if (!isAbortError && attempt < retries) {
        attempt += 1;
        await sleep(retryDelayMs * attempt);
        continue;
      }
      throw error;
    }
  }
}

export function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError) {
    if (error.detail) return error.detail;
    if (error.message) return error.message;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export function toResourceIssue(error: unknown, fallback: string): ResourceIssue {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        kind: "unauthorized",
        message: getErrorMessage(error, fallback),
        retryable: false,
      };
    }
    if (error.status === 403) {
      return {
        kind: "forbidden",
        message: getErrorMessage(error, fallback),
        retryable: false,
      };
    }
    if (
      error.status === 408 ||
      error.status === 429 ||
      (typeof error.status === "number" && error.status >= 500)
    ) {
      return {
        kind: "transient-error",
        message: getErrorMessage(error, fallback),
        retryable: true,
      };
    }
  }

  return {
    kind: "error",
    message: getErrorMessage(error, fallback),
    retryable: false,
  };
}
