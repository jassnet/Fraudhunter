import type { NextRequest } from "next/server";

import { proxyToBackend } from "@/lib/server/backend-proxy";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  return proxyToBackend({
    path: "/api/console/alerts",
    search: request.nextUrl.search,
    auth: "read",
  });
}
