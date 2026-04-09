import { headers as nextHeaders } from "next/headers";

export type ConsoleViewerRole = "analyst" | "admin";

export type ConsoleViewer = {
  userId: string;
  email: string;
  role: ConsoleViewerRole;
  requestId: string;
};

const ROLE_RANK: Record<ConsoleViewerRole, number> = {
  analyst: 1,
  admin: 2,
};

class ConsoleAuthError extends Error {
  status: number;

  constructor(message: string, status = 403) {
    super(message);
    this.name = "ConsoleAuthError";
    this.status = status;
  }
}

function firstHeaderValue(headers: Headers, name: string) {
  return headers.get(name)?.trim() ?? "";
}

function normalizeRole(value: string): ConsoleViewerRole | null {
  return value === "analyst" || value === "admin" ? value : null;
}

function requireViewerFromHeaders(headers: Headers, minimumRole: ConsoleViewerRole): ConsoleViewer {
  const userId = firstHeaderValue(headers, "X-Auth-Request-User");
  const email = firstHeaderValue(headers, "X-Auth-Request-Email");
  const role = normalizeRole(firstHeaderValue(headers, "X-Auth-Request-Role"));

  if (!userId || !email || !role) {
    throw new ConsoleAuthError("Console gateway identity is required.");
  }
  if (ROLE_RANK[role] < ROLE_RANK[minimumRole]) {
    throw new ConsoleAuthError("Forbidden", 403);
  }

  return {
    userId,
    email,
    role,
    requestId: crypto.randomUUID(),
  };
}

export function requireConsoleViewer(request: Request, minimumRole: ConsoleViewerRole): ConsoleViewer {
  return requireViewerFromHeaders(request.headers, minimumRole);
}

export async function getConsoleViewer(minimumRole: ConsoleViewerRole = "analyst"): Promise<ConsoleViewer> {
  const headers = new Headers(await nextHeaders());
  return requireViewerFromHeaders(headers, minimumRole);
}

export function toConsoleAuthErrorResponse(error: unknown) {
  if (error instanceof ConsoleAuthError) {
    return Response.json({ detail: error.message }, { status: error.status });
  }
  throw error;
}
