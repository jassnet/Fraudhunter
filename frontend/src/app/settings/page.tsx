"use client";

import { useEffect, useState } from "react";
import { Separator } from "@/components/ui/separator";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { RefreshCw, Save, Database, CheckCircle, XCircle } from "lucide-react";
import { getSettings, updateSettings, syncMasters, getMastersStatus, Settings } from "@/lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncingMasters, setSyncingMasters] = useState(false);
  const [mastersStatus, setMastersStatus] = useState<{
    media_count: number;
    promotion_count: number;
    user_count: number;
  } | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadSettings = async () => {
    try {
      const data = await getSettings();
      setSettings(data);
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

  const handleSave = async () => {
    if (!settings) return;
    setSaving(true);
    setMessage(null);
    try {
      await updateSettings(settings);
      setMessage({ type: 'success', text: '設定を保存しました' });
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
  };

  if (loading) {
    return (
      <div className="space-y-6 p-10 pb-16">
        <Skeleton className="h-8 w-[200px]" />
        <Skeleton className="h-4 w-[300px]" />
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
      <div className="space-y-6 p-10 pb-16">
        <div className="text-center py-8 text-red-500">
          設定の読み込みに失敗しました。バックエンドが起動しているか確認してください。
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-10 pb-16 md:block">
      {message && (
        <div className={`flex items-center gap-2 p-4 rounded-lg ${
          message.type === 'success' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
        }`}>
          {message.type === 'success' ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
          {message.text}
        </div>
      )}

      <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
        <div className="flex-1 lg:max-w-2xl">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>クリック検知閾値（同一IP/UA）</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="click_threshold">1日あたりのクリック数上限</Label>
                  <Input
                    id="click_threshold"
                    type="number"
                    value={settings.click_threshold}
                    onChange={(e) => updateField('click_threshold', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="media_threshold">重複媒体数上限</Label>
                  <Input
                    id="media_threshold"
                    type="number"
                    value={settings.media_threshold}
                    onChange={(e) => updateField('media_threshold', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="program_threshold">重複案件数上限</Label>
                  <Input
                    id="program_threshold"
                    type="number"
                    value={settings.program_threshold}
                    onChange={(e) => updateField('program_threshold', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="burst_click_threshold">バースト検知クリック数</Label>
                  <Input
                    id="burst_click_threshold"
                    type="number"
                    value={settings.burst_click_threshold}
                    onChange={(e) => updateField('burst_click_threshold', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="burst_window_seconds">バースト検知時間窓（秒）</Label>
                  <Input
                    id="burst_window_seconds"
                    type="number"
                    value={settings.burst_window_seconds}
                    onChange={(e) => updateField('burst_window_seconds', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>成果検知閾値（同一IP/UA）</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="conversion_threshold">1日あたりの成果数上限</Label>
                  <Input
                    id="conversion_threshold"
                    type="number"
                    value={settings.conversion_threshold}
                    onChange={(e) => updateField('conversion_threshold', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="conv_media_threshold">重複媒体数上限</Label>
                  <Input
                    id="conv_media_threshold"
                    type="number"
                    value={settings.conv_media_threshold}
                    onChange={(e) => updateField('conv_media_threshold', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="conv_program_threshold">重複案件数上限</Label>
                  <Input
                    id="conv_program_threshold"
                    type="number"
                    value={settings.conv_program_threshold}
                    onChange={(e) => updateField('conv_program_threshold', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="burst_conversion_threshold">バースト検知成果数</Label>
                  <Input
                    id="burst_conversion_threshold"
                    type="number"
                    value={settings.burst_conversion_threshold}
                    onChange={(e) => updateField('burst_conversion_threshold', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="burst_conversion_window_seconds">バースト検知時間窓（秒）</Label>
                  <Input
                    id="burst_conversion_window_seconds"
                    type="number"
                    value={settings.burst_conversion_window_seconds}
                    onChange={(e) => updateField('burst_conversion_window_seconds', parseInt(e.target.value) || 0)}
                    min={1}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>フィルタ設定</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>ブラウザのみ</Label>
                  </div>
                  <Switch
                    checked={settings.browser_only}
                    onCheckedChange={(checked) => updateField('browser_only', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>データセンターIP除外</Label>
                  </div>
                  <Switch
                    checked={settings.exclude_datacenter_ip}
                    onCheckedChange={(checked) => updateField('exclude_datacenter_ip', checked)}
                  />
                </div>
              </CardContent>
            </Card>
            
            <div className="flex justify-end">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                変更を保存
              </Button>
            </div>
          </div>
        </div>

        {/* サイドバー：マスタ管理 */}
        <div className="w-full lg:w-80">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                マスタデータ
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {mastersStatus && (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">媒体数</span>
                    <span className="font-medium">{mastersStatus.media_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">案件数</span>
                    <span className="font-medium">{mastersStatus.promotion_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">ユーザー数</span>
                    <span className="font-medium">{mastersStatus.user_count}</span>
                  </div>
                </div>
              )}
              <Button
                variant="outline"
                className="w-full"
                onClick={handleSyncMasters}
                disabled={syncingMasters}
              >
                {syncingMasters ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
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
