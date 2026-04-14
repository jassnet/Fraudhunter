import { SettingsScreen } from "@/features/console/settings-screen";
import { getConsoleViewer } from "@/lib/server/console-auth";

export default async function SettingsPage() {
  await getConsoleViewer();
  return <SettingsScreen />;
}
