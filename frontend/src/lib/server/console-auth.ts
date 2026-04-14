import { headers as nextHeaders } from "next/headers";

export type ConsoleViewer = {
  userId: string;
  email: string;
  requestId: string;
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

function resolveDevViewer(): ConsoleViewer | null {
  const env = (process.env.FC_ENV ?? "").trim().toLowerCase();
  const userId = (process.env.FC_DEV_CONSOLE_USER ?? "").trim();
  const email = (process.env.FC_DEV_CONSOLE_EMAIL ?? "").trim();

  if (env !== "dev") {
    return null;
  }
  if (!userId || !email) {
    return null;
  }

  return {
    userId,
    email,
    requestId: crypto.randomUUID(),
  };
}

function requireViewerFromHeaders(headers: Headers): ConsoleViewer {
  const userId = firstHeaderValue(headers, "X-Auth-Request-User");
  const email = firstHeaderValue(headers, "X-Auth-Request-Email");

  if (!userId || !email) {
    const devViewer = resolveDevViewer();
    if (devViewer) {
      return devViewer;
    }
    throw new ConsoleAuthError("Console gateway identity is required.");
  }

  return {
    userId,
    email,
    requestId: crypto.randomUUID(),
  };
}

export function requireConsoleViewer(request: Request): ConsoleViewer {
  return requireViewerFromHeaders(request.headers);
}

export async function getConsoleViewer(): Promise<ConsoleViewer> {
  const headers = new Headers(await nextHeaders());
  return requireViewerFromHeaders(headers);
}

export function toConsoleAuthErrorResponse(error: unknown) {
  if (error instanceof ConsoleAuthError) {
    return Response.json({ detail: error.message }, { status: error.status });
  }
  throw error;
}
