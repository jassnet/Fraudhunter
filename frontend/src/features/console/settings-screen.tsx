"use client";

import { useEffect, useState } from "react";

import { useConsoleDisplayMode } from "@/components/console-display-mode";
import { ActionButton, ErrorState, LoadingState, PageHeader, Panel } from "@/components/console-ui";
import { getConsoleSettings, updateConsoleSettings } from "@/lib/console-api";
import type { ConsoleSettings, ConsoleSettingsUpdateResponse } from "@/lib/console-types";

const SETTING_SECTIONS: Array<{
  title: string;
  description: string;
  fields: Array<{ key: keyof ConsoleSettings; label: string; type: "number" | "boolean" }>;
}> = [
  {
    title: "クリックの異常判定",
    description: "クリック数や短時間集中の判定しきい値です。",
    fields: [
      { key: "click_threshold", label: "クリック数のしきい値", type: "number" },
      { key: "media_threshold", label: "媒体の分散数のしきい値", type: "number" },
      { key: "program_threshold", label: "案件の分散数のしきい値", type: "number" },
      { key: "burst_click_threshold", label: "短時間集中クリックのしきい値", type: "number" },
      { key: "burst_window_seconds", label: "短時間集中と判定する秒数", type: "number" },
    ],
  },
  {
    title: "成果（コンバージョン）の異常判定",
    description: "成果の件数や発生タイミングの判定しきい値です。",
    fields: [
      { key: "conversion_threshold", label: "成果件数のしきい値", type: "number" },
      { key: "conv_media_threshold", label: "成果が発生した媒体の分散数のしきい値", type: "number" },
      { key: "conv_program_threshold", label: "成果が発生した案件の分散数のしきい値", type: "number" },
      { key: "burst_conversion_threshold", label: "短時間集中成果のしきい値", type: "number" },
      { key: "burst_conversion_window_seconds", label: "短時間集中と判定する秒数", type: "number" },
      { key: "min_click_to_conv_seconds", label: "クリックから成果までの最短秒数", type: "number" },
      { key: "max_click_to_conv_seconds", label: "クリックから成果までの最長秒数", type: "number" },
    ],
  },
  {
    title: "不正の疑いを示す兆候",
    description: "確認／追跡／操作の各観点から不正兆候を判定するしきい値です。",
    fields: [
      { key: "fraud_check_min_total", label: "確認処理の最小件数", type: "number" },
      { key: "fraud_check_invalid_rate", label: "確認処理の無効率", type: "number" },
      { key: "fraud_check_duplicate_plid_count", label: "PLIDの重複件数", type: "number" },
      { key: "fraud_check_duplicate_plid_rate", label: "PLIDの重複率", type: "number" },
      { key: "fraud_track_min_total", label: "追跡処理の最小件数", type: "number" },
      { key: "fraud_track_auth_error_rate", label: "認証エラー率", type: "number" },
      { key: "fraud_track_auth_ip_ua_rate", label: "IPアドレス/ブラウザ情報の認証率", type: "number" },
      { key: "fraud_action_min_total", label: "操作の最小件数", type: "number" },
      { key: "fraud_action_short_gap_seconds", label: "短い間隔と判定する秒数", type: "number" },
      { key: "fraud_action_short_gap_count", label: "短い間隔の件数しきい値", type: "number" },
      { key: "fraud_action_cancel_rate", label: "キャンセル率", type: "number" },
      { key: "fraud_action_fixed_gap_min_count", label: "同一間隔の最小件数", type: "number" },
      { key: "fraud_action_fixed_gap_max_unique", label: "同一間隔と判定する種類の上限", type: "number" },
      { key: "fraud_spike_multiplier", label: "急増と判定する倍率", type: "number" },
      { key: "fraud_spike_lookback_days", label: "急増判定の比較日数", type: "number" },
    ],
  },
  {
    title: "追加の絞り込み条件",
    description: "アクセス元の除外やブラウザ判定のルールです。",
    fields: [
      { key: "browser_only", label: "ブラウザからのアクセスのみを対象にする", type: "boolean" },
      { key: "exclude_datacenter_ip", label: "データセンターのIPアドレスを除外する", type: "boolean" },
    ],
  },
];

export function SettingsScreen() {
  const { showAdvanced, setShowAdvanced } = useConsoleDisplayMode();
  const [data, setData] = useState<ConsoleSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [result, setResult] = useState<ConsoleSettingsUpdateResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await getConsoleSettings();
        if (!cancelled) {
          setData(response);
        }
      } catch (caughtError) {
        if (!cancelled) {
          setError(caughtError instanceof Error ? caughtError.message : "設定の取得に失敗しました。");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  function setField<K extends keyof ConsoleSettings>(key: K, value: ConsoleSettings[K]) {
    setData((current) => (current ? { ...current, [key]: value } : current));
  }

  async function handleSave() {
    if (!data) {
      return;
    }
    setSaving(true);
    setError(null);
    setFeedback(null);
    try {
      const response = await updateConsoleSettings(data);
      setResult(response);
      setFeedback("設定を更新しました。");
      setData(response.settings);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "設定の更新に失敗しました。");
    } finally {
      setSaving(false);
    }
  }

  if (!showAdvanced) {
    return (
      <div className="screen-page">
        <PageHeader
          title="検知設定"
          description="通常表示では非表示です。必要なときだけ詳細表示に切り替えて確認できます。"
        />
        <Panel title="通常表示では非表示です" description="しきい値の変更や再計算は、管理判断が必要な操作です。">
          <div className="screen-page">
            <p className="table-secondary">日常のレビュー導線では表示せず、必要なときだけまとめて表示します。</p>
            <ActionButton onClick={() => setShowAdvanced(true)}>詳細表示に切り替える</ActionButton>
          </div>
        </Panel>
      </div>
    );
  }

  return (
    <div className="screen-page">
      <PageHeader
        title="検知設定"
        description="検知ルールのしきい値を管理します。保存すると検知結果が自動で再計算されます。"
        actions={
          <ActionButton onClick={() => void handleSave()} disabled={loading || saving || !data}>
            この内容で保存する
          </ActionButton>
        }
      />

      {loading && !data ? <LoadingState /> : null}
      {error ? <ErrorState message={error} /> : null}
      {feedback ? (
        <div className="success-message" role="status" aria-live="polite">
          {feedback}
        </div>
      ) : null}

      {result ? (
        <Panel title="保存結果" description="設定の保存と検知結果の再計算の状況です。">
          <div className="detail-meta-block">
            <div className="detail-meta-row">
              <span>設定の保存</span>
              <span className="detail-meta-value">{result.persisted ? "保存できました" : "注意事項あり"}</span>
            </div>
            <div className="detail-meta-row">
              <span>検知結果の再計算</span>
              <span className="detail-meta-value">
                {result.findings_recompute_enqueued
                  ? `${result.recompute_job_ids?.length ?? 0}件の再計算を開始しました`
                  : result.findings_recomputed
                    ? "すぐに反映されました"
                    : "再計算は行われませんでした"}
              </span>
            </div>
            {result.warning ? (
              <div className="detail-meta-row">
                <span>注意事項</span>
                <span className="detail-meta-value detail-break">{result.warning}</span>
              </div>
            ) : null}
          </div>
        </Panel>
      ) : null}

      {data ? (
        <div className="settings-grid">
          {SETTING_SECTIONS.map((section) => (
            <Panel key={section.title} title={section.title} description={section.description}>
              <div className="settings-fields">
                {section.fields.map((field) => (
                  <label key={field.key} className="form-field">
                    <span>{field.label}</span>
                    {field.type === "boolean" ? (
                      <input
                        type="checkbox"
                        checked={Boolean(data[field.key])}
                        onChange={(event) => setField(field.key, event.target.checked as ConsoleSettings[typeof field.key])}
                      />
                    ) : (
                      <input
                        type="number"
                        value={String(data[field.key])}
                        onChange={(event) => setField(field.key, Number(event.target.value) as ConsoleSettings[typeof field.key])}
                      />
                    )}
                  </label>
                ))}
              </div>
            </Panel>
          ))}
        </div>
      ) : null}
    </div>
  );
}
