"use client";

import { useEffect, useMemo, useState } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { RefreshCw, Save, Database, CheckCircle, XCircle, HelpCircle } from "lucide-react";
import { getSettings, updateSettings, syncMasters, getMastersStatus, Settings } from "@/lib/api";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

// 各設定項目の説明
const FIELD_DESCRIPTIONS: Record<keyof Settings, { label: string; description: string; min: number; max?: number; recommended?: string }> = {
  click_threshold: {
    label: "1日あたりのクリック数上限",
    description: "同一IP/UAからの1日のクリック数がこの値以上で不正疑惑としてマーク",
    min: 1,
    max: 10000,
    recommended: "推奨: 30〜100",
  },
  media_threshold: {
    label: "重複メディア数上限",
    description: "同じIP/UAから複数のメディアへアクセスした場合に不正疑惑としてマーク",
    min: 1,
    max: 100,
    recommended: "推奨: 2〜5",
  },
  program_threshold: {
    label: "重複案件数上限",
    description: "同一IP/UAが複数の案件にアクセスした場合に不正疑惑としてマーク",
    min: 1,
    max: 100,
    recommended: "推奨: 2〜5",
  },
  burst_click_threshold: {
    label: "バースト検知クリック数",
    description: "短時間内にこの数以上のクリックがあった場合にバースト検知",
    min: 1,
    max: 1000,
    recommended: "推奨: 10〜30",
  },
  burst_window_seconds: {
    label: "バースト検知時間窓（秒）",
    description: "バースト検知の対象となる時間範囲（秒）",
    min: 1,
    max: 86400,
    recommended: "推奨: 300〜900（5〜15分）",
  },
  conversion_threshold: {
    label: "1日あたりの成果数上限",
    description: "同一IP/UAからの1日の成果数がこの値以上で不正疑惑としてマーク",
    min: 1,
    max: 1000,
    recommended: "推奨: 3〜10",
  },
  conv_media_threshold: {
    label: "重複メディア数上限",
    description: "同じIP/UAから複数のメディアで成果を上げた場合に不正疑惑としてマーク",
    min: 1,
    max: 100,
    recommended: "推奨: 2〜3",
  },
  conv_program_threshold: {
    label: "重複案件数上限",
    description: "同一IP/UAが複数の案件で成果を上げた場合に不正疑惑としてマーク",
    min: 1,
    max: 100,
    recommended: "推奨: 2〜3",
  },
  burst_conversion_threshold: {
    label: "バースト検知成果数",
    description: "短時間内にこの数以上の成果があった場合にバースト検知",
    min: 1,
    max: 100,
    recommended: "推奨: 2〜5",
  },
  burst_conversion_window_seconds: {
    label: "バースト検知時間窓（秒）",
    description: "成果バースト検知の対象となる時間範囲（秒）",
    min: 1,
    max: 86400,
    recommended: "推奨: 1800〜3600（30分〜1時間）",
  },
  min_click_to_conv_seconds: {
    label: "クリック→成果 最短経過時間（秒）",
    description: "クリックから成果までの時間がこの値未満の場合に不正疑惑としてマーク。0で無効。",
    min: 0,
    max: 86400,
    recommended: "推奨: 5〜30",
  },
  max_click_to_conv_seconds: {
    label: "クリック→成果 最長経過時間（秒）",
    description: "クリックから成果までの時間がこの値を超える場合に不正疑惑としてマーク。30日（2592000秒）が目安。",
    min: 0,
    max: 31536000,
    recommended: "推奨: 2592000（30日）",
  },
  browser_only: {
    label: "ブラウザのみ",
    description: "ブラウザ由来のUser-Agentのみを検知対象とする。ボットやAPIアクセスを除外。",
    min: 0,
  },
  exclude_datacenter_ip: {
    label: "データセンターIP除外",
    description: "AWS、GCP等のデータセンターIPレンジを検知対象から除外する。",
    min: 0,
  },
};

interface FieldInputProps {
  id: keyof Settings;
  value: number;
  onChange: (value: number) => void;
  error?: string;
}

function FieldInput({ id, value, onChange, error }: FieldInputProps) {
  const field = FIELD_DESCRIPTIONS[id];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (val == "") {
      return;
    }
    const num = Number(val);
    if (!Number.isNaN(num)) onChange(num);
  };

  const handleBlur = () => {
    if (value < field.min) {
      onChange(field.min);
      return;
    }
    if (field.max !== undefined && value > field.max) {
      onChange(field.max);
    }
  };

  return (
    <div className="grid gap-2">
      <div className="flex items-center gap-2">
        <Label htmlFor={id} className="text-pretty">{field.label}</Label>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                className="inline-flex h-4 w-4 items-center justify-center text-muted-foreground"
                aria-label={`${field.label}の説明`}
              >
                <HelpCircle className="h-4 w-4" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="right" className="max-w-xs">
              <p className="text-sm text-pretty">{field.description}</p>
              {field.recommended && (
                <p className="mt-1 text-xs text-pretty text-muted-foreground">{field.recommended}</p>
              )}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      <Input
        id={id}
        name={id}
        type="number"
        value={Number.isFinite(value) ? value : ""}
        onChange={handleChange}
        onBlur={handleBlur}
        min={field.min}
        max={field.max}
        autoComplete="off"
        className={cn("tabular-nums", error && "border-destructive")}
      />
      {error && (
        <p className="text-xs text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [initialSettings, setInitialSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncingMasters, setSyncingMasters] = useState(false);
  const [mastersStatus, setMastersStatus] = useState<{
    media_count: number;
    promotion_count: number;
    user_count: number;
  } | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [errors, setErrors] = useState<Partial<Record<keyof Settings, string>>>({});

  const loadSettings = async () => {
    try {
      const data = await getSettings();
      setSettings(data);
      setInitialSettings(data);
    } catch (err) {
      console.error("Failed to load settings", err);
      setMessage({ type: 'error', text: '設定の読み込みに失敗しました' });
    } finally {
      setLoading(false);
    }
  };

  const loadMastersStatus = async () => {
    try {
      const data = await getMastersStatus();
      setMastersStatus(data);
    } catch (err) {
      console.error("Failed to load masters status", err);
    }
  };

  useEffect(() => {
    loadSettings();
    loadMastersStatus();
  }, []);

  const isDirty = useMemo(() => {
    if (!settings || !initialSettings) return false;
    return JSON.stringify(settings) !== JSON.stringify(initialSettings);
  }, [settings, initialSettings]);

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (!isDirty) return;
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [isDirty]);

  const validateSettings = (settings: Settings): Partial<Record<keyof Settings, string>> => {
    const errors: Partial<Record<keyof Settings, string>> = {};
    
    for (const [key, field] of Object.entries(FIELD_DESCRIPTIONS)) {
      const k = key as keyof Settings;
      const value = settings[k];
      
      if (typeof value === "number") {
        if (value < field.min) {
          errors[k] = `${field.min}以上の値を入力してください`;
        }
        if (field.max !== undefined && value > field.max) {
          errors[k] = `${field.max}以下の値を入力してください`;
        }
      }
    }
    
    return errors;
  };

  const handleSave = async () => {
    if (!settings) return;
    
    const validationErrors = validateSettings(settings);
    setErrors(validationErrors);
    
    if (Object.keys(validationErrors).length > 0) {
      setMessage({ type: 'error', text: '入力値にエラーがあります' });
      return;
    }
    
    setSaving(true);
    setMessage(null);
    try {
      await updateSettings(settings);
      setMessage({ type: 'success', text: '設定を保存しました' });
      setInitialSettings(settings);
      setTimeout(() => setMessage(null), 3000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '保存に失敗しました';
      setMessage({ type: 'error', text: message });
    } finally {
      setSaving(false);
    }
  };

  const handleSyncMasters = async () => {
    setSyncingMasters(true);
    setMessage(null);
    try {
      await syncMasters();
      setMessage({ type: 'success', text: 'マスタ同期を開始しました。完了までしばらくお待ちください。' });
      // 少し待ってから再読み込み
      setTimeout(loadMastersStatus, 5000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'マスタ同期の開始に失敗しました';
      setMessage({ type: 'error', text: message });
    } finally {
      setSyncingMasters(false);
    }
  };

  const updateField = (field: keyof Settings, value: number | boolean) => {
    if (!settings) return;
    setSettings({ ...settings, [field]: value });
    // エラーをクリア
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6 sm:p-8">
        <div className="space-y-2">
          <Skeleton className="h-7 w-[160px]" />
          <Skeleton className="h-4 w-[260px]" />
        </div>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-[200px] rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="space-y-6 p-6 sm:p-8">
        <div className="space-y-1">
          <h1 className="text-balance text-2xl font-semibold">設定</h1>
          <p className="text-pretty text-sm text-muted-foreground">
            不正検知の閾値とフィルタを管理します。
          </p>
        </div>
        <Card className="border-destructive/40">
          <CardHeader>
            <CardTitle className="text-balance text-destructive">設定の読み込みに失敗しました</CardTitle>
            <CardDescription className="text-pretty">
              バックエンドが起動しているか確認してから、再読み込みしてください。
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={loadSettings}>
              再読み込み
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 sm:p-8">
      <div className="space-y-1">
        <h1 className="text-balance text-2xl font-semibold">設定</h1>
        <p className="text-pretty text-sm text-muted-foreground">
          不正検知の閾値とフィルタを管理します。
        </p>
      </div>

      {message && (
        <div
          className={cn(
            "flex items-center gap-2 rounded-lg border px-4 py-3 text-sm",
            message.type === "success"
              ? "border-green-500/30 bg-green-500/10 text-green-500"
              : "border-red-500/30 bg-red-500/10 text-red-500"
          )}
          role="status"
          aria-live="polite"
        >
          {message.type === "success" ? (
            <CheckCircle className="h-4 w-4" />
          ) : (
            <XCircle className="h-4 w-4" />
          )}
          <span className="text-pretty">{message.text}</span>
        </div>
      )}

      <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
        <div className="flex-1 lg:max-w-2xl">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-balance">クリック検知閾値（同一IP/UA）</CardTitle>
                <CardDescription className="text-pretty">
                  同一のIPアドレスとUser-Agentの組み合わせからのクリックを分析し、
                  不正の可能性があるアクセスを検知するための閾値を設定します。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <FieldInput
                  id="click_threshold"
                  value={settings.click_threshold}
                  onChange={(v) => updateField('click_threshold', v)}
                  error={errors.click_threshold}
                />
                <FieldInput
                  id="media_threshold"
                  value={settings.media_threshold}
                  onChange={(v) => updateField('media_threshold', v)}
                  error={errors.media_threshold}
                />
                <FieldInput
                  id="program_threshold"
                  value={settings.program_threshold}
                  onChange={(v) => updateField('program_threshold', v)}
                  error={errors.program_threshold}
                />
                <FieldInput
                  id="burst_click_threshold"
                  value={settings.burst_click_threshold}
                  onChange={(v) => updateField('burst_click_threshold', v)}
                  error={errors.burst_click_threshold}
                />
                <FieldInput
                  id="burst_window_seconds"
                  value={settings.burst_window_seconds}
                  onChange={(v) => updateField('burst_window_seconds', v)}
                  error={errors.burst_window_seconds}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-balance">成果検知閾値（同一IP/UA）</CardTitle>
                <CardDescription className="text-pretty">
                  同一のIPアドレスとUser-Agentの組み合わせからの成果（コンバージョン）を分析し、
                  不正の可能性がある成果を検知するための閾値を設定します。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <FieldInput
                  id="conversion_threshold"
                  value={settings.conversion_threshold}
                  onChange={(v) => updateField('conversion_threshold', v)}
                  error={errors.conversion_threshold}
                />
                <FieldInput
                  id="conv_media_threshold"
                  value={settings.conv_media_threshold}
                  onChange={(v) => updateField('conv_media_threshold', v)}
                  error={errors.conv_media_threshold}
                />
                <FieldInput
                  id="conv_program_threshold"
                  value={settings.conv_program_threshold}
                  onChange={(v) => updateField('conv_program_threshold', v)}
                  error={errors.conv_program_threshold}
                />
                <FieldInput
                  id="burst_conversion_threshold"
                  value={settings.burst_conversion_threshold}
                  onChange={(v) => updateField('burst_conversion_threshold', v)}
                  error={errors.burst_conversion_threshold}
                />
                <FieldInput
                  id="burst_conversion_window_seconds"
                  value={settings.burst_conversion_window_seconds}
                  onChange={(v) => updateField('burst_conversion_window_seconds', v)}
                  error={errors.burst_conversion_window_seconds}
                />
                <FieldInput
                  id="min_click_to_conv_seconds"
                  value={settings.min_click_to_conv_seconds}
                  onChange={(v) => updateField('min_click_to_conv_seconds', v)}
                  error={errors.min_click_to_conv_seconds}
                />
                <FieldInput
                  id="max_click_to_conv_seconds"
                  value={settings.max_click_to_conv_seconds}
                  onChange={(v) => updateField('max_click_to_conv_seconds', v)}
                  error={errors.max_click_to_conv_seconds}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-balance">フィルタ設定</CardTitle>
                <CardDescription className="text-pretty">
                  検知対象を絞り込むためのフィルタ設定です。
                  誤検知を減らしたい場合に有効化してください。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="browser_only">{FIELD_DESCRIPTIONS.browser_only.label}</Label>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              className="inline-flex h-4 w-4 items-center justify-center text-muted-foreground"
                              aria-label={`${FIELD_DESCRIPTIONS.browser_only.label}の説明`}
                            >
                              <HelpCircle className="h-4 w-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="right" className="max-w-xs">
                            <p className="text-sm text-pretty">{FIELD_DESCRIPTIONS.browser_only.description}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    <p className="text-xs text-pretty text-muted-foreground">
                      ボットやAPIアクセスを除外
                    </p>
                  </div>
                  <Switch
                    id="browser_only"
                    name="browser_only"
                    checked={settings.browser_only}
                    onCheckedChange={(checked) => updateField('browser_only', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="exclude_datacenter_ip">
                        {FIELD_DESCRIPTIONS.exclude_datacenter_ip.label}
                      </Label>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              className="inline-flex h-4 w-4 items-center justify-center text-muted-foreground"
                              aria-label={`${FIELD_DESCRIPTIONS.exclude_datacenter_ip.label}の説明`}
                            >
                              <HelpCircle className="h-4 w-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="right" className="max-w-xs">
                            <p className="text-sm text-pretty">
                              {FIELD_DESCRIPTIONS.exclude_datacenter_ip.description}
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    <p className="text-xs text-pretty text-muted-foreground">
                      AWS/GCP等のクラウドIPを除外
                    </p>
                  </div>
                  <Switch
                    id="exclude_datacenter_ip"
                    name="exclude_datacenter_ip"
                    checked={settings.exclude_datacenter_ip}
                    onCheckedChange={(checked) => updateField('exclude_datacenter_ip', checked)}
                  />
                </div>
              </CardContent>
            </Card>
            
            <div className="flex justify-end">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? <RefreshCw className="mr-2 h-4 w-4 motion-safe:animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                変更を保存
              </Button>
            </div>
          </div>
        </div>

        {/* サイドバー：マスタ管理 */}
        <div className="w-full lg:w-80">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-balance">
                <Database className="h-5 w-5" />
                マスタデータ
              </CardTitle>
              <CardDescription className="text-pretty">
                ACSから媒体・案件・ユーザー情報を同期します。
                名前表示に必要です。
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {mastersStatus && (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">媒体数</span>
                    <span className="font-medium tabular-nums">{mastersStatus.media_count.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">案件数</span>
                    <span className="font-medium tabular-nums">{mastersStatus.promotion_count.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">ユーザー数</span>
                    <span className="font-medium tabular-nums">{mastersStatus.user_count.toLocaleString()}</span>
                  </div>
                </div>
              )}
              {!mastersStatus && (
                <div className="text-sm text-pretty text-muted-foreground text-center py-4">
                  マスタデータが未同期です
                </div>
              )}
              <Button
                variant="outline"
                className="w-full"
                onClick={handleSyncMasters}
                disabled={syncingMasters}
              >
                {syncingMasters ? (
                  <RefreshCw className="mr-2 h-4 w-4 motion-safe:animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                ACSから同期
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
