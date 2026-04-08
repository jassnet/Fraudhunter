type ProxyAuth = "read" | "admin";

function resolveBackendBaseUrl() {
  return (process.env.FC_BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001").replace(
    /\/$/,
    "",
  );
}

function applyAuthHeaders(headers: Headers, auth: ProxyAuth) {
  if (auth === "admin") {
    const adminToken = process.env.FC_ADMIN_API_KEY;
    if (!adminToken) {
      throw new Error("FC_ADMIN_API_KEY is not configured.");
    }
    headers.set("X-API-Key", adminToken);
    return;
  }

  const readToken = process.env.FC_READ_API_KEY;
  if (!readToken) {
    throw new Error("FC_READ_API_KEY is not configured.");
  }
  headers.set("X-Read-API-Key", readToken);
}

type ProxyRequest = {
  path: string;
  search?: string;
  method?: string;
  body?: string;
  auth?: ProxyAuth;
};

export async function proxyToBackend({
  path,
  search = "",
  method = "GET",
  body,
  auth = "read",
}: ProxyRequest) {
  try {
    const headers = new Headers({
      Accept: "application/json",
    });
    if (body) {
      headers.set("Content-Type", "application/json");
    }
    applyAuthHeaders(headers, auth);

    const response = await fetch(`${resolveBackendBaseUrl()}${path}${search}`, {
      method,
      headers,
      body,
      cache: "no-store",
    });
    const contentType = response.headers.get("content-type") ?? "application/json; charset=utf-8";
    const contentDisposition = response.headers.get("content-disposition");

    return new Response(await response.text(), {
      status: response.status,
      headers: {
        "content-type": contentType,
        ...(contentDisposition ? { "content-disposition": contentDisposition } : {}),
      },
    });
  } catch (caughtError) {
    const detail =
      caughtError instanceof Error ? caughtError.message : "バックエンドへの接続に失敗しました。";
    return Response.json({ detail }, { status: 502 });
  }
}
