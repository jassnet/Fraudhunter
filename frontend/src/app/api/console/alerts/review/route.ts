import { proxyToBackend } from "@/lib/server/backend-proxy";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  return proxyToBackend({
    path: "/api/console/alerts/review",
    method: "POST",
    body: await request.text(),
    auth: "admin",
  });
}
