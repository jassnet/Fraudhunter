import { requireConsoleViewer, toConsoleAuthErrorResponse } from "@/lib/server/console-auth";
import { proxyToBackend } from "@/lib/server/backend-proxy";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    return proxyToBackend({
      path: "/api/console/alerts/follow-up",
      method: "POST",
      body: await request.text(),
      viewer: requireConsoleViewer(request),
    });
  } catch (error) {
    return toConsoleAuthErrorResponse(error);
  }
}
