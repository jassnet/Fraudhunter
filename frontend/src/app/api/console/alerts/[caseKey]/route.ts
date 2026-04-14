import { requireConsoleViewer, toConsoleAuthErrorResponse } from "@/lib/server/console-auth";
import { proxyToBackend } from "@/lib/server/backend-proxy";

export const dynamic = "force-dynamic";

type AlertDetailRouteProps = {
  params: Promise<{
    caseKey: string;
  }>;
};

export async function GET(_request: Request, { params }: AlertDetailRouteProps) {
  try {
    const { caseKey } = await params;
    return proxyToBackend({
      path: `/api/console/alerts/${encodeURIComponent(caseKey)}`,
      viewer: requireConsoleViewer(_request),
    });
  } catch (error) {
    return toConsoleAuthErrorResponse(error);
  }
}
