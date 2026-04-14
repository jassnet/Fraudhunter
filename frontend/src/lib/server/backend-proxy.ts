import { createHmac } from "crypto";

import type { ConsoleViewer } from "@/lib/server/console-auth";

function resolveBackendBaseUrl() {
  return (process.env.FC_BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001").replace(
    /\/$/,
    "",
  );
}

function signViewer(viewer: ConsoleViewer) {
  const secret = process.env.FC_INTERNAL_PROXY_SECRET;
  if (!secret) {
    throw new Error("FC_INTERNAL_PROXY_SECRET is not configured.");
  }
  return createHmac("sha256", secret)
    .update(`${viewer.userId}\n${viewer.email}\n${viewer.requestId}`, "utf-8")
    .digest("hex");
}

function applyViewerHeaders(headers: Headers, viewer: ConsoleViewer) {
  headers.set("X-Console-User-Id", viewer.userId);
  headers.set("X-Console-User-Email", viewer.email);
  headers.set("X-Console-Request-Id", viewer.requestId);
  headers.set("X-Console-User-Signature", signViewer(viewer));
}

type ProxyRequest = {
  path: string;
  search?: string;
  method?: string;
  body?: string;
  viewer: ConsoleViewer;
};

export async function proxyToBackend({
  path,
  search = "",
  method = "GET",
  body,
  viewer,
}: ProxyRequest) {
  try {
    const headers = new Headers({
      Accept: "application/json",
    });
    if (body) {
      headers.set("Content-Type", "application/json");
    }
    applyViewerHeaders(headers, viewer);

    const response = await fetch(`${resolveBackendBaseUrl()}${path}${search}`, {
      method,
      headers,
      body,
      cache: "no-store",
    });
    const contentType = response.headers.get("content-type") ?? "application/json; charset=utf-8";
    const contentDisposition = response.headers.get("content-disposition");

    return new Response(await response.text(), {
      status: response.status,
      headers: {
        "content-type": contentType,
        ...(contentDisposition ? { "content-disposition": contentDisposition } : {}),
      },
    });
  } catch (caughtError) {
    const detail =
      caughtError instanceof Error ? caughtError.message : "バックエンドへの接続に失敗しました。";
    return Response.json({ detail }, { status: 502 });
  }
}
