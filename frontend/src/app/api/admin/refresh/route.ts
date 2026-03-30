import { proxyAdminRequest } from "@/app/api/admin/_lib/proxy";

export async function POST(request: Request) {
  const body = await request.text();
  return proxyAdminRequest("/api/refresh", {
    method: "POST",
    body,
  });
}
