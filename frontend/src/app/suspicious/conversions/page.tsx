import { redirect } from "next/navigation";

export default function SuspiciousConversionsAliasPage({
  searchParams,
}: {
  searchParams?: Record<string, string | string[] | undefined>;
}) {
  const params = new URLSearchParams();
  for (const [key, raw] of Object.entries(searchParams || {})) {
    if (typeof raw === "string") params.set(key, raw);
    if (Array.isArray(raw) && raw[0]) params.set(key, raw[0]);
  }
  const query = params.toString();
  redirect(query ? `/suspicious/fraud?${query}` : "/suspicious/fraud");
}
