"use client";

import { useCallback, useEffect, useState } from "react";
import { getHealthStatus, HealthIssue } from "@/lib/api";
import { AlertTriangle, XCircle, AlertCircle, ChevronDown, ChevronUp, X } from "lucide-react";
import { Button } from "@/components/ui/button";

export function SetupWarning() {
  const [issues, setIssues] = useState<HealthIssue[]>([]);
  const [status, setStatus] = useState<'ok' | 'warning' | 'error' | 'loading'>('loading');
  const [expanded, setExpanded] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const checkHealth = useCallback(async () => {
    try {
      const health = await getHealthStatus();
      setStatus(health.status);
      setIssues(health.issues);
    } catch (e) {
      console.error("Health check failed", e);
      setStatus('error');
      setIssues([{
        type: 'error',
        field: 'connection',
        message: 'バックエンドに接続できません',
        hint: 'バックエンドサーバーが起動しているか確認してください'
      }]);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    // 30秒ごとに再チェック
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  if (status === 'loading' || status === 'ok' || dismissed) {
    return null;
  }

  const errors = issues.filter(i => i.type === 'error');
  const warnings = issues.filter(i => i.type === 'warning');

  return (
    <div className={`border-b ${status === 'error' ? 'bg-red-500/10 border-red-500/20' : 'bg-yellow-500/10 border-yellow-500/20'}`}>
      <div className="px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {status === 'error' ? (
              <XCircle className="h-5 w-5 text-red-500" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
            )}
            <span className={`font-medium ${status === 'error' ? 'text-red-600 dark:text-red-400' : 'text-yellow-600 dark:text-yellow-400'}`}>
              {status === 'error' ? 'セットアップが必要です' : '確認が必要な項目があります'}
            </span>
            <span className="text-sm text-muted-foreground">
              {errors.length > 0 && `エラー: ${errors.length}件`}
              {errors.length > 0 && warnings.length > 0 && ' / '}
              {warnings.length > 0 && `警告: ${warnings.length}件`}
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
                  閉じる
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-1" />
                  詳細
                </>
              )}
            </Button>
            {status === 'warning' && (
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
                  issue.type === 'error' 
                    ? 'bg-red-500/10' 
                    : 'bg-yellow-500/10'
                }`}
              >
                <AlertCircle className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                  issue.type === 'error' ? 'text-red-500' : 'text-yellow-500'
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

