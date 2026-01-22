"use client";

import { useEffect, useState, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RefreshCw, Clock, Pause, Play } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface LastUpdatedProps {
  lastUpdated: Date | null;
  onRefresh: () => Promise<void>;
  isRefreshing?: boolean;
  showAutoRefresh?: boolean;
  autoRefreshInterval?: number; // milliseconds
  className?: string;
}

const AUTO_REFRESH_OPTIONS = [
  { label: "30秒", value: 30000 },
  { label: "1分", value: 60000 },
  { label: "5分", value: 300000 },
  { label: "10分", value: 600000 },
];

function formatElapsed(date: Date): string {
  const now = new Date();
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diff < 5) return "たった今";
  if (diff < 60) return `${diff}秒前`;
  if (diff < 3600) return `${Math.floor(diff / 60)}分前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}時間前`;
  return `${Math.floor(diff / 86400)}日前`;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function LastUpdated({
  lastUpdated,
  onRefresh,
  isRefreshing = false,
  showAutoRefresh = true,
  autoRefreshInterval: initialInterval,
  className = "",
}: LastUpdatedProps) {
  const [elapsed, setElapsed] = useState<string>("");
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(false);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState(
    initialInterval || 60000
  );

  // 経過時間の更新
  useEffect(() => {
    if (!lastUpdated) return;

    const updateElapsed = () => {
      setElapsed(formatElapsed(lastUpdated));
    };

    updateElapsed();
    const interval = setInterval(updateElapsed, 1000);
    return () => clearInterval(interval);
  }, [lastUpdated]);

  // 自動更新
  useEffect(() => {
    if (!autoRefreshEnabled || isRefreshing) return;

    const interval = setInterval(() => {
      onRefresh();
    }, autoRefreshInterval);

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, autoRefreshInterval, isRefreshing, onRefresh]);

  const handleRefresh = useCallback(async () => {
    await onRefresh();
  }, [onRefresh]);


  const selectAutoRefreshInterval = (interval: number) => {
    setAutoRefreshInterval(interval);
    setAutoRefreshEnabled(true);
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* 最終更新時刻表示 */}
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge
              variant="outline"
              className="flex items-center gap-1.5 px-2 py-1 font-normal cursor-default"
            >
              <Clock className="h-3 w-3" />
              <span className="text-xs">
                {lastUpdated ? elapsed : "未取得"}
              </span>
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>最終更新: {lastUpdated ? formatTime(lastUpdated) : "-"}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* 更新ボタン */}
      <Button
        variant="outline"
        size="sm"
        onClick={handleRefresh}
        disabled={isRefreshing}
        className="h-8"
      >
        <RefreshCw
          className={`mr-1.5 h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`}
        />
        更新
      </Button>

      {/* 自動更新設定 */}
      {showAutoRefresh && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant={autoRefreshEnabled ? "default" : "outline"}
              size="sm"
              className="h-8 px-2"
            >
              {autoRefreshEnabled ? (
                <Play className="h-3.5 w-3.5" />
              ) : (
                <Pause className="h-3.5 w-3.5" />
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel className="text-xs">自動更新</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuCheckboxItem
              checked={!autoRefreshEnabled}
              onCheckedChange={() => setAutoRefreshEnabled(false)}
            >
              オフ
            </DropdownMenuCheckboxItem>
            {AUTO_REFRESH_OPTIONS.map((option) => (
              <DropdownMenuCheckboxItem
                key={option.value}
                checked={autoRefreshEnabled && autoRefreshInterval === option.value}
                onCheckedChange={() => selectAutoRefreshInterval(option.value)}
              >
                {option.label}ごと
              </DropdownMenuCheckboxItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  );
}

