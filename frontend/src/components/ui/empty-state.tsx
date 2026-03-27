import type { ReactNode } from "react";
import { StatePanel } from "@/components/ui/state-panel";

interface EmptyStateProps {
  title: string;
  message?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ title, message, action, className }: EmptyStateProps) {
  return <StatePanel title={title} message={message} action={action} className={className} />;
}
