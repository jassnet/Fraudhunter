import { DashboardScreen } from "@/features/console/dashboard-screen";
import { getConsoleViewer } from "@/lib/server/console-auth";

export default async function DashboardPage() {
  const viewer = await getConsoleViewer();
  return <DashboardScreen viewerRole={viewer.role} />;
}
