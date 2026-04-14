import { requireConsoleViewer, toConsoleAuthErrorResponse } from "@/lib/server/console-auth";
import { proxyToBackend } from "@/lib/server/backend-proxy";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    return proxyToBackend({
      path: "/api/console/settings",
      viewer: requireConsoleViewer(request),
    });
  } catch (error) {
    return toConsoleAuthErrorResponse(error);
  }
}

export async function POST(request: Request) {
  try {
    return proxyToBackend({
      path: "/api/console/settings",
      method: "POST",
      body: await request.text(),
      viewer: requireConsoleViewer(request),
    });
  } catch (error) {
    return toConsoleAuthErrorResponse(error);
  }
}
