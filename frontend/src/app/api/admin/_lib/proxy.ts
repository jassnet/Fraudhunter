import { NextResponse } from "next/server";

const backendBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const isProduction = process.env.NODE_ENV === "production";

function buildBackendHeaders(contentType?: string) {
  const headers = new Headers();
  if (contentType) {
    headers.set("Content-Type", contentType);
  }

  const adminApiKey = process.env.FC_ADMIN_API_KEY;
  if (adminApiKey) {
    headers.set("X-API-Key", adminApiKey);
  }

  return headers;
}

export async function proxyAdminRequest(
  path: string,
  init: RequestInit = {}
) {
  if (isProduction && !process.env.FC_ADMIN_API_KEY) {
    return NextResponse.json(
      { detail: "admin capability unavailable" },
      { status: 403 }
    );
  }

  const response = await fetch(`${backendBaseUrl}${path}`, {
    ...init,
    headers: buildBackendHeaders(
      init.body ? "application/json" : undefined
    ),
    cache: "no-store",
  });

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const payload = await response.json();
    return NextResponse.json(payload, { status: response.status });
  }

  const text = await response.text();
  return new NextResponse(text, {
    status: response.status,
    headers: contentType ? { "content-type": contentType } : undefined,
  });
}
