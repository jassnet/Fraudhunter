import { proxyToBackend } from "@/lib/server/backend-proxy";

export const dynamic = "force-dynamic";

type AlertDetailRouteProps = {
  params: Promise<{
    findingKey: string;
  }>;
};

export async function GET(_request: Request, { params }: AlertDetailRouteProps) {
  const { findingKey } = await params;
  return proxyToBackend({
    path: `/api/console/alerts/${encodeURIComponent(findingKey)}`,
    auth: "read",
  });
}
