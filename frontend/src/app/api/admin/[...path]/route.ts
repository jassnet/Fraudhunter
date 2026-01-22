import { NextRequest } from "next/server";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8001";
const ADMIN_API_KEY = process.env.FC_ADMIN_API_KEY;

const ALLOWED_METHODS = new Set(["GET", "POST"]);

type RouteContext = {
  params: Promise<{
    path: string[];
  }>;
};

function buildUpstreamUrl(request: NextRequest, pathSegments: string[]) {
  const url = new URL(`/api/${pathSegments.join("/")}`, API_BASE_URL);
  url.search = request.nextUrl.search;
  return url;
}

async function proxyAdminRequest(request: NextRequest, ctx: RouteContext) {
  if (!ADMIN_API_KEY) {
    return Response.json(
      { detail: "FC_ADMIN_API_KEY is not configured" },
      { status: 500 }
    );
  }

  const { path: pathSegments } = await ctx.params;
  if (pathSegments.length === 0) {
    return Response.json({ detail: "Missing admin path" }, { status: 400 });
  }

  if (!ALLOWED_METHODS.has(request.method)) {
    return new Response("Method Not Allowed", { status: 405 });
  }

  const upstreamUrl = buildUpstreamUrl(request, pathSegments);
  const headers = new Headers(request.headers);
  headers.set("X-API-Key", ADMIN_API_KEY);
  headers.delete("host");
  headers.delete("connection");
  headers.delete("content-length");
  headers.delete("cookie");

  const init: RequestInit = {
    method: request.method,
    headers,
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    const body = await request.arrayBuffer();
    if (body.byteLength > 0) {
      init.body = body;
    }
  }

  const res = await fetch(upstreamUrl, init);
  const responseHeaders = new Headers(res.headers);
  return new Response(res.body, { status: res.status, headers: responseHeaders });
}

export const runtime = "nodejs";

export async function GET(request: NextRequest, ctx: RouteContext) {
  return proxyAdminRequest(request, ctx);
}

export async function POST(request: NextRequest, ctx: RouteContext) {
  return proxyAdminRequest(request, ctx);
}
