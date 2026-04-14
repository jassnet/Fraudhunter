import { DashboardScreen } from "@/features/console/dashboard-screen";
import { getConsoleViewer } from "@/lib/server/console-auth";

type DashboardPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function DashboardPage({ searchParams }: DashboardPageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : {};
  await getConsoleViewer();
  return <DashboardScreen searchParams={resolvedSearchParams} />;
}
