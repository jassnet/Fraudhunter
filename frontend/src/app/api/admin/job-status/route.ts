import { proxyAdminRequest } from "@/app/api/admin/_lib/proxy";

export async function GET() {
  return proxyAdminRequest("/api/job/status/admin");
}
