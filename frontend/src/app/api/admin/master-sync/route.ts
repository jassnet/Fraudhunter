import { proxyAdminRequest } from "@/app/api/admin/_lib/proxy";

export async function POST() {
  return proxyAdminRequest("/api/sync/masters", { method: "POST" });
}
