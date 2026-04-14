import { AlertsScreen } from "@/features/console/alerts-screen";
import { getConsoleViewer } from "@/lib/server/console-auth";

type AlertsPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function AlertsPage({ searchParams }: AlertsPageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : {};
  await getConsoleViewer();

  return <AlertsScreen searchParams={resolvedSearchParams} />;
}
