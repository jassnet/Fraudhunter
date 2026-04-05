import { AlertDetailScreen } from "@/features/console/alert-detail-screen";

type AlertDetailPageProps = {
  params: Promise<{
    findingKey: string;
  }>;
};

export default async function AlertDetailPage({ params }: AlertDetailPageProps) {
  const { findingKey } = await params;
  return <AlertDetailScreen findingKey={findingKey} />;
}
