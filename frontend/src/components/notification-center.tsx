"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type NoticeVariant = "info" | "success" | "warning" | "error";

type Notice = {
  id: string;
  title: string;
  description?: string;
  variant?: NoticeVariant;
  duration?: number | null;
};

type NotificationsContextValue = {
  notify: (notice: Omit<Notice, "id">) => string;
  dismiss: (id: string) => void;
};

const NotificationsContext = createContext<NotificationsContextValue | null>(null);

const DEFAULT_DURATION = 6000;

const variantStyles: Record<NoticeVariant, { icon: typeof Info; className: string }> = {
  info: { icon: Info, className: "border-border bg-background text-foreground" },
  success: { icon: CheckCircle2, className: "border-green-500/30 bg-green-500/10 text-green-700 dark:text-green-400" },
  warning: { icon: AlertTriangle, className: "border-yellow-500/30 bg-yellow-500/10 text-yellow-700 dark:text-yellow-400" },
  error: { icon: XCircle, className: "border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-400" },
};

function NotificationCenter({
  notices,
  onDismiss,
}: {
  notices: Notice[];
  onDismiss: (id: string) => void;
}) {
  return (
    <div
      className={cn(
        "fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-2 pr-[env(safe-area-inset-right)] pt-[env(safe-area-inset-top)]"
      )}
      aria-live="polite"
    >
      {notices.map((notice) => {
        const variant = notice.variant || "info";
        const Icon = variantStyles[variant].icon;
        return (
          <div
            key={notice.id}
            role={variant === "error" ? "alert" : "status"}
            className={cn(
              "flex items-start gap-3 rounded-lg border p-3 shadow-sm",
              variantStyles[variant].className
            )}
          >
            <Icon className="mt-0.5 h-4 w-4" aria-hidden="true" />
            <div className="min-w-0 flex-1 space-y-1">
              <div className="text-sm font-medium text-balance">{notice.title}</div>
              {notice.description && (
                <div className="text-xs text-pretty text-muted-foreground">{notice.description}</div>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => onDismiss(notice.id)}
              aria-label="通知を閉じる"
              className="mt-0.5"
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
        );
      })}
    </div>
  );
}

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const [notices, setNotices] = useState<Notice[]>([]);
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismiss = useCallback((id: string) => {
    setNotices((prev) => prev.filter((notice) => notice.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const notify = useCallback(
    (notice: Omit<Notice, "id">) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const duration = notice.duration ?? DEFAULT_DURATION;
      const nextNotice: Notice = { id, ...notice };

      setNotices((prev) => [nextNotice, ...prev].slice(0, 5));

      if (duration && duration > 0) {
        const timer = setTimeout(() => dismiss(id), duration);
        timers.current.set(id, timer);
      }

      return id;
    },
    [dismiss]
  );

  const value = useMemo(() => ({ notify, dismiss }), [notify, dismiss]);

  return (
    <NotificationsContext.Provider value={value}>
      {children}
      <NotificationCenter notices={notices} onDismiss={dismiss} />
    </NotificationsContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationsContext);
  if (!context) {
    throw new Error("useNotifications must be used within NotificationsProvider");
  }
  return context;
}
