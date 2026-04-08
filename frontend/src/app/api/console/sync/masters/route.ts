import { proxyToBackend } from "@/lib/server/backend-proxy";

export const dynamic = "force-dynamic";

export async function POST() {
  return proxyToBackend({
    path: "/api/sync/masters",
    method: "POST",
    auth: "admin",
  });
}
