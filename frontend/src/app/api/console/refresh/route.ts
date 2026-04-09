import { requireConsoleViewer, toConsoleAuthErrorResponse } from "@/lib/server/console-auth";
import { proxyToBackend } from "@/lib/server/backend-proxy";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    return proxyToBackend({
      path: "/api/console/admin/refresh",
      method: "POST",
      body: await request.text(),
      viewer: requireConsoleViewer(request, "admin"),
    });
  } catch (error) {
    return toConsoleAuthErrorResponse(error);
  }
}
