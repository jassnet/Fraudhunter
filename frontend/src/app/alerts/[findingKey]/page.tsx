import { AlertDetailScreen } from "@/features/console/alert-detail-screen";
import { getConsoleViewer } from "@/lib/server/console-auth";

type AlertDetailPageProps = {
  params: Promise<{
    findingKey: string;
  }>;
};

export default async function AlertDetailPage({ params }: AlertDetailPageProps) {
  const { findingKey } = await params;
  const viewer = await getConsoleViewer();
  return <AlertDetailScreen findingKey={findingKey} viewerRole={viewer.role} />;
}
