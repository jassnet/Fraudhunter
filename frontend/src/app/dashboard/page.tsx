import { DashboardScreen } from "@/features/console/dashboard-screen";

export default function DashboardPage() {
  return <DashboardScreen adminActionsEnabled={Boolean(process.env.FC_ADMIN_API_KEY)} />;
}
