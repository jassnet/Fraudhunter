import { Suspense } from "react";
import FraudListPage from "@/features/fraud-list/fraud-list-page";

export default function SuspiciousFraudPage() {
  return (
    <Suspense fallback={null}>
      <FraudListPage />
    </Suspense>
  );
}
