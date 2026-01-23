"use client";

import { useState } from "react";
import { useHealthStatus } from "@/hooks/use-health-status";
import { AlertTriangle, XCircle, AlertCircle, ChevronDown, ChevronUp, X } from "lucide-react";
import { Button } from "@/components/ui/button";

export function SetupWarning() {
  const { status, issues } = useHealthStatus();
  const [expanded, setExpanded] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  if (status === "loading" || status === "ok" || dismissed) {
    return null;
  }

  const errors = issues.filter((i) => i.type === "error");
  const warnings = issues.filter((i) => i.type === "warning");

  return (
    <div className={`border-b ${status === "error" ? "bg-red-500/10 border-red-500/20" : "bg-yellow-500/10 border-yellow-500/20"}`}>
      <div className="px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {status === "error" ? (
              <XCircle className="h-5 w-5 text-red-500" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
            )}
            <span className={`font-medium ${status === "error" ? "text-red-600 dark:text-red-400" : "text-yellow-600 dark:text-yellow-400"}`}>
              {status === "error" ? "Setup error detected" : "Warnings detected"}
            </span>
            <span className="text-sm text-muted-foreground">
              {errors.length > 0 && `Errors: ${errors.length}`}
              {errors.length > 0 && warnings.length > 0 && " / "}
              {warnings.length > 0 && `Warnings: ${warnings.length}`}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              className="h-7 px-2"
            >
              {expanded ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-1" />
                  Collapse
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-1" />
                  Details
                </>
              )}
            </Button>
            {status === "warning" && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setDismissed(true)}
                className="h-7 px-2"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {expanded && (
          <div className="mt-3 space-y-2">
            {issues.map((issue, idx) => (
              <div
                key={idx}
                className={`flex items-start gap-2 p-2 rounded ${
                  issue.type === "error"
                    ? "bg-red-500/10"
                    : "bg-yellow-500/10"
                }`}
              >
                <AlertCircle className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                  issue.type === "error" ? "text-red-500" : "text-yellow-500"
                }`} />
                <div className="text-sm">
                  <div className="font-medium">{issue.message}</div>
                  <div className="text-muted-foreground text-xs mt-0.5">
                    {issue.hint}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
