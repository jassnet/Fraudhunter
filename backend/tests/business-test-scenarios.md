# Fraud Checker 業務テストシナリオ一覧

このドキュメントは、非技術者でも「何を守るテストか」を理解できるように整理しています。  
シナリオIDごとに、業務上の意味・失敗時の影響・自動テストの対応を明示します。

## 判定基準

- 自動化状態:
  - `自動`: pytest で継続実行
  - `統合`: DB環境が必要（`FRAUD_TEST_DATABASE_URL`）
- 対象範囲: 不正検知、取り込み、集計、運用安全、設定反映、マスタ同期

## シナリオ一覧

### SC-01 クリック大量発生を検知する

- 業務上の状況: 同じ端末から短時間に大量クリックが発生
- 期待する結果: 不正候補として「クリック数過多」「短時間集中」を表示
- 失敗時の影響: 明らかな不正トラフィックの見逃し
- 自動化状態: 自動

### SC-02 成果までが短すぎる不自然な経路を検知する

- 業務上の状況: 成果件数は少なくても時間差が異常
- 期待する結果: 時間差異常として不正候補に追加
- 失敗時の影響: 自動化成果の兆候見逃し
- 自動化状態: 自動

### SC-03 成果の短時間集中を検知する

- 業務上の状況: 成果が短い時間窓に集中
- 期待する結果: バースト理由で警告
- 失敗時の影響: 成果水増しの初動遅れ
- 自動化状態: 自動

### SC-04 誤検知対象（非ブラウザ/データセンターIP）を除外する

- 業務上の状況: 調査対象を実運用に絞りたい
- 期待する結果: 除外条件に合うアクセスは不正候補から外す
- 失敗時の影響: 調査工数増加とノイズ増加
- 自動化状態: 自動

### SC-05 クリックと成果の両方で怪しい端末を高リスク扱いにする

- 業務上の状況: 二重に疑わしい端末を優先対応したい
- 期待する結果: 高リスク一覧に入る
- 失敗時の影響: 重大案件の優先順位誤り
- 自動化状態: 自動

### SC-06 管理者APIを保護する

- 業務上の状況: 管理機能への不正アクセス防止
- 期待する結果: 認証不備は `401`
- 失敗時の影響: 管理機能の不正利用
- 自動化状態: 自動

### SC-07 入力日付ミスを即時検出する

- 業務上の状況: オペレーション時の入力ミス
- 期待する結果: 不正日付は `400` で明示
- 失敗時の影響: 誤ジョブ実行、問い合わせ増加
- 自動化状態: 自動

### SC-08 ジョブ同時実行を防止する

- 業務上の状況: 実行中に再実行要求が来る
- 期待する結果: `409` で競合を返す
- 失敗時の影響: 重複実行による不整合
- 自動化状態: 自動

### SC-09 定期更新の集計結果を日付単位で返す

- 業務上の状況: 直近N時間の監視数字確認
- 期待する結果: クリック・成果・検知件数が日付ごとに返る
- 失敗時の影響: 監視レポート不信
- 自動化状態: 自動

### SC-10 日次サマリーと前日比較を返す

- 業務上の状況: 日次報告で増減を判断
- 期待する結果: 当日値と前日値を同時に返す
- 失敗時の影響: KPI判断ミス
- 自動化状態: 自動

### SC-11 日次時系列をクリック/成果で統合表示する

- 業務上の状況: データが片側だけ存在する日もある
- 期待する結果: 欠損値を0補完して時系列を返す
- 失敗時の影響: ダッシュボードの時系列崩れ
- 自動化状態: 自動

### SC-12 設定変更を保存し、反映可否を返す

- 業務上の状況: 閾値変更の運用
- 期待する結果: 保存成功/失敗を応答で判別できる
- 失敗時の影響: 設定反映漏れの見逃し
- 自動化状態: 自動

### SC-13 マスタ同期の実行結果件数を返す

- 業務上の状況: 参照マスタ更新作業
- 期待する結果: 同期件数を返し、完了可否がわかる
- 失敗時の影響: マスタ更新状況の不透明化
- 自動化状態: 自動

### SC-14 DB接続ありの最小スモークを確認する

- 業務上の状況: DB接続/スキーマの最低保証
- 期待する結果: 疎通と基本クエリが成功
- 失敗時の影響: 本番運用前の初期障害見逃し
- 自動化状態: 統合

### SC-15 外部ACS APIのレスポンスを業務データへ正しく変換する

- 業務上の状況: クリック/成果/マスタデータを取得して日次処理へ渡す
- 期待する結果: 認証付き取得、日時範囲指定、必要項目の変換が正しい
- 失敗時の影響: 取り込み件数や不正判定精度が低下
- 自動化状態: 自動

### SC-16 設定値とマスタ統計の永続データを業務形式で返す

- 業務上の状況: 設定画面・運用監視で保存済みデータを利用する
- 期待する結果: JSON復元、件数集計、最終同期時刻を正しく返す
- 失敗時の影響: 運用判断ミスや設定反映漏れの見逃し
- 自動化状態: 自動

### SC-17 時刻とDB接続設定の基盤ロジックを正しく扱う

- 業務上の状況: タイムゾーン設定やDB接続URLの誤りは全体動作に影響する
- 期待する結果: 時刻解釈と接続文字列正規化が一貫して動作する
- 失敗時の影響: 取り込み対象期間ずれ、接続障害
- 自動化状態: 自動

### SC-18 ジョブ状態の永続管理を正しく行う

- 業務上の状況: 長時間処理の開始/完了/失敗を運用画面で追跡する
- 期待する結果: 状態更新と結果JSON保存が一貫して行われる
- 失敗時の影響: ジョブ監視不能、再実行判断ミス
- 自動化状態: 自動

### SC-19 CLI運用コマンドを安全に実行する

- 業務上の状況: 定期バッチや手動保守でCLIを実行する
- 期待する結果: オプション整合性チェック、更新処理、マスタ同期処理が期待どおりに完了する
- 失敗時の影響: 運用ジョブ失敗、誤実行、データ更新漏れ
- 自動化状態: 自動

## シナリオIDとテスト対応表


| シナリオID | 主なテスト関数                                                                                                                                                               |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SC-01  | `test_click_detector_applies_threshold_and_burst_reason`, `test_suspicious_clicks_returns_business_friendly_fields`                                                   |
| SC-02  | `test_conversion_detector_adds_gap_only_findings`                                                                                                                     |
| SC-03  | `test_format_reasons_and_risk_scoring_reflect_business_priority`, `test_conversion_burst_threshold_is_used`                                                           |
| SC-04  | `test_conversion_detector_respects_browser_and_datacenter_filters`                                                                                                    |
| SC-05  | `test_combined_detector_marks_intersection_as_high_risk`                                                                                                              |
| SC-06  | `test_health_requires_admin_token`                                                                                                                                    |
| SC-07  | `test_ingest_clicks_rejects_invalid_date`, `test_suspicious_conversions_rejects_invalid_date`                                                                         |
| SC-08  | `test_refresh_returns_conflict_when_job_is_running`, `test_enqueue_job_raises_conflict_when_another_job_is_running`                                                   |
| SC-09  | `test_run_refresh_collects_detect_results_per_date`, `test_run_refresh_without_detect_does_not_build_detection`                                                       |
| SC-10  | `test_get_summary_returns_business_facing_totals`, `test_summary_endpoint_returns_payload`                                                                            |
| SC-11  | `test_get_daily_stats_merges_click_and_conversion_rows`, `test_daily_stats_endpoint_returns_data`                                                                     |
| SC-12  | `test_update_settings_returns_persisted_true_when_save_succeeds`, `test_update_settings_returns_warning_when_save_fails`, `test_settings_endpoints_use_service_layer` |
| SC-13  | `test_run_master_sync_returns_upsert_counts`, `test_sync_masters_enqueues_background_job`, `test_masters_status_returns_repository_stats`                             |
| SC-14  | `test_postgres_smoke`                                                                                                                                                 |
| SC-15  | `test_fetch_click_logs_returns_click_models_and_auth_header`, `test_fetch_conversion_logs_maps_entry_fields`, `test_fetch_master_endpoints_map_records`, `test_fetch_all_master_methods_iterate_pages_until_short_page` |
| SC-16  | `test_get_all_masters_returns_counts_and_last_synced`, `test_load_settings_parses_json_and_keeps_plain_text` |
| SC-17  | `test_parse_datetime_handles_epoch_seconds_and_milliseconds`, `test_today_local_uses_configured_timezone`, `test_normalize_database_url_converts_postgres_prefixes`, `test_get_engine_uses_explicit_url` |
| SC-18  | `test_ensure_schema_creates_table_and_inserts_singleton_row`, `test_start_returns_true_when_update_succeeds`, `test_finish_serializes_result_and_executes_update` |
| SC-19  | `test_cmd_refresh_rejects_conflicting_flags`, `test_cmd_refresh_runs_ingestion_and_detection`, `test_cmd_sync_masters_updates_all_master_types`, `test_main_prints_help_and_returns_1_for_unknown_command` |


## 現時点で対象外

- 本番相当のフルE2E（UI経由）
- 大規模データの性能試験
