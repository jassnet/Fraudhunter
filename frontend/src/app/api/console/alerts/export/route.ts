import type { NextRequest } from "next/server";

import { requireConsoleViewer, toConsoleAuthErrorResponse } from "@/lib/server/console-auth";
import { proxyToBackend } from "@/lib/server/backend-proxy";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    return proxyToBackend({
      path: "/api/console/alerts/export",
      search: request.nextUrl.search,
      viewer: requireConsoleViewer(request, "analyst"),
    });
  } catch (error) {
    return toConsoleAuthErrorResponse(error);
  }
}
