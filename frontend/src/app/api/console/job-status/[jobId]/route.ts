import { requireConsoleViewer, toConsoleAuthErrorResponse } from "@/lib/server/console-auth";
import { proxyToBackend } from "@/lib/server/backend-proxy";

export const dynamic = "force-dynamic";

type JobStatusRouteProps = {
  params: Promise<{
    jobId: string;
  }>;
};

export async function GET(request: Request, { params }: JobStatusRouteProps) {
  try {
    const { jobId } = await params;
    return proxyToBackend({
      path: `/api/console/job-status/${encodeURIComponent(jobId)}`,
      viewer: requireConsoleViewer(request, "analyst"),
    });
  } catch (error) {
    return toConsoleAuthErrorResponse(error);
  }
}
