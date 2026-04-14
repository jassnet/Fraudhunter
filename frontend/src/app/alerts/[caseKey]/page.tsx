import { AlertDetailScreen } from "@/features/console/alert-detail-screen";
import { getConsoleViewer } from "@/lib/server/console-auth";

type AlertDetailPageProps = {
  params: Promise<{
    caseKey: string;
  }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function firstSearchParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

export default async function AlertDetailPage({ params, searchParams }: AlertDetailPageProps) {
  const { caseKey } = await params;
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const viewer = await getConsoleViewer();
  return (
    <AlertDetailScreen
      caseKey={caseKey}
      viewerUserId={viewer.userId}
      returnTo={firstSearchParam(resolvedSearchParams.returnTo)}
    />
  );
}
