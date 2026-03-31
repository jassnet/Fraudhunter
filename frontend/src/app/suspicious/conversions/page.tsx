import { Suspense } from "react";
import SuspiciousListPage from "@/features/suspicious-list/suspicious-list-page";

export default function SuspiciousConversionsPage() {
  return (
    <Suspense fallback={null}>
      <SuspiciousListPage />
    </Suspense>
  );
}
