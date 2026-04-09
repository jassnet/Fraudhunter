import { AlertDetailScreen } from "@/features/console/alert-detail-screen";
import { getConsoleViewer } from "@/lib/server/console-auth";

type AlertDetailPageProps = {
  params: Promise<{
    caseKey: string;
  }>;
};

export default async function AlertDetailPage({ params }: AlertDetailPageProps) {
  const { caseKey } = await params;
  const viewer = await getConsoleViewer();
  return <AlertDetailScreen caseKey={caseKey} viewerRole={viewer.role} />;
}
