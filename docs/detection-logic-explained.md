# 検知ロジックのやさしい説明

このファイルは、いまの fraud monitoring システムが「何を見て、どういう基準で怪しいと判断しているか」を、実装に沿ってやさしく説明するためのものです。

実装の正本は以下です。

- `backend/src/fraud_checker/suspicious.py`
- `backend/src/fraud_checker/config.py`
- `backend/src/fraud_checker/services/settings.py`
- `backend/src/fraud_checker/repositories/reporting_read.py`

## 1. まず全体像

いまの検知は、ざっくり言うと次の流れです。

1. ACS API からクリック系ログとコンバージョン系ログを取得する
2. 1日単位で `IP + User-Agent` ごとにまとめる
3. 「件数が多すぎる」「媒体またぎが多い」「案件またぎが多い」「短時間に集中しすぎる」などの条件に当てはまるかを見る
4. 条件に当てはまった `IP + User-Agent` を suspicious finding として保存する
5. 同じ日にクリック側でも CV 側でも引っかかった `IP + User-Agent` は、特に強く注意すべき対象として扱う

重要なのは、UI がその場で計算しているわけではないことです。  
判定は backend 側で先に計算して PostgreSQL に保存してあり、UI はそれを読むだけです。

## 2. 何のログを使っているか

### クリック側

クリック側の主データは `track_log/search` です。

理由:

- `IP`
- `User-Agent`
- `referrer`
- 媒体
- 案件

のような、不正判定に必要な情報を持ちやすいからです。

このプロジェクトでは、一般的な「クリック数」というより、実態は「トラッキング記録数」に近いです。  
そのため、UI でも `クリック数` ではなく `トラッキング数` と表現する方向に寄せています。

### コンバージョン側

コンバージョン側の主データは `action_log_raw` です。

理由:

- 成果の生ログに近い
- `entry_ipaddress`
- `entry_useragent`
- click から conversion までの時間差

のような情報を使えるからです。

## 3. どの単位で怪しさを見るか

いまの基本単位は、次のまとまりです。

- 日付
- IP アドレス
- User-Agent

つまり「同じ日」「同じ IP」「同じ UA」でどれだけ動いているかを見ています。

クリック側も CV 側も、この `1日 × IP × UA` という考え方が中心です。

## 4. クリック側の判定

クリック側では、`1日 × IP × UA` ごとに次を見ています。

- その組み合わせの総トラッキング数
- 何媒体にまたがっているか
- 何案件にまたがっているか
- 短時間に集中しているか

### 現在のデフォルト閾値

- `click_threshold = 50`
- `media_threshold = 3`
- `program_threshold = 3`
- `burst_click_threshold = 20`
- `burst_window_seconds = 600`

### クリック側で suspicious になる条件

次のどれかを満たすと suspicious です。

1. 総トラッキング数が 50 以上
2. 媒体数が 3 以上
3. 案件数が 3 以上
4. 総トラッキング数が 20 以上で、最初から最後までが 600 秒以内

### 例

- 同じ IP / UA で 80 回流入している
- 同じ IP / UA が 5 媒体にまたがっている
- 同じ IP / UA が 4 案件にまたがっている
- 同じ IP / UA が 10 分以内に 25 回出ている

こういうものがクリック側の suspicious として出ます。

## 5. コンバージョン側の判定

CV 側でも、`1日 × IP × UA` ごとに次を見ています。

- CV 数
- 何媒体にまたがっているか
- 何案件にまたがっているか
- 短時間に CV が集中しているか
- click から conversion までの時間差が不自然ではないか

### 現在のデフォルト閾値

- `conversion_threshold = 5`
- `conv_media_threshold = 2`
- `conv_program_threshold = 2`
- `burst_conversion_threshold = 3`
- `burst_conversion_window_seconds = 1800`
- `min_click_to_conv_seconds = 5`
- `max_click_to_conv_seconds = 2592000`

### コンバージョン側で suspicious になる条件

次のどれかを満たすと suspicious です。

1. CV 数が 5 以上
2. 媒体数が 2 以上
3. 案件数が 2 以上
4. CV 数が 3 以上で、最初から最後までが 1800 秒以内
5. click から conversion までが 5 秒未満
6. click から conversion までが 30 日超

### 例

- 同じ IP / UA で 7 CV 出ている
- 同じ IP / UA が複数媒体や複数案件にまたがって CV している
- 30 分以内に 4 CV 集中している
- click の 2 秒後に CV している

こういうものが CV 側の suspicious として出ます。

## 6. 高リスクとは何か

いまの実装では、同じ日に同じ `IP + UA` が

- クリック側でも suspicious
- コンバージョン側でも suspicious

になっていると、特に強く注意すべき対象とみなします。

これは

- 流入も怪しい
- 成果も怪しい
- しかも同じ主体に見える

という意味だからです。

コード上では `CombinedSuspiciousDetector` がこの重なりを見ています。

## 7. これは「断定」ではなく「レビュー優先順位」

このシステムは、現時点では「不正を断定するシステム」ではありません。

役割は次です。

- 先に人が見るべき対象を絞る
- 同じパターンが繰り返し出ていないかを監視する
- suspicious clicks / suspicious conversions を一覧で追えるようにする

つまり、最終判断は人手レビュー前提です。

## 8. 欠損データがあるときの注意

二次卸や計測条件の差で、次の欠損は起こりえます。

- IP が弱い
- User-Agent が欠ける
- click と conversion の結びつきが薄い
- referrer が空になる

この場合の注意点:

- 欠損があるから即 fraud ではない
- 逆に、欠損があると怪しさが弱くしか見えないこともある
- つまり「見えないから安全」とは言えない

なので、いまのロジックは「広く拾って人が確認する」寄りです。

## 9. いまのフィルタ設定

現状のデフォルトでは、次はオフです。

- `browser_only = false`
- `exclude_datacenter_ip = false`

意味:

- ブラウザっぽい UA だけに絞っていない
- データセンター IP を除外していない

この設定は、取りこぼしを減らす代わりに広めに拾います。

## 10. 数が少なく見えることがある理由

「ACS にはもっとログがあるのに、画面では少なく見える」というケースはありえます。

主な理由は次です。

### 定期 refresh は小さい窓で動く

通常の定期 refresh は短い時間窓で回ります。  
そのため、直近分の鮮度は高い一方で、どこかの時間帯で失敗すると欠ける可能性があります。

### backfill は欠損補完のために別で動く

このプロジェクトでは、欠損補完のために `直近24時間の backfill` を前提にしています。

つまり:

- 通常運転: 小さい時間窓で追いかける
- 補完: 24 時間窓で取り直す

という 2 段構えです。

## 11. いまのロジックの強み

- 単純で説明しやすい
- 保存済み findings を使うので UI が速い
- クリック側と CV 側を別々に見つつ、重なりも見られる
- 閾値を設定で調整できる

## 12. いまのロジックの限界

- ルールベースなので、巧妙な fraud を取りこぼす可能性がある
- 欠損が多い系列では、強い断定に向かない
- IP / UA ベースなので、端末共有や NAT の影響を受ける
- 「なぜ正常か」は説明できず、「なぜ怪しいか」を説明する形

## 13. 運用としてどう読むべきか

おすすめの読み方は次です。

1. まず dashboard で全体の傾向を見る
2. suspicious clicks / suspicious conversions で件数の多いものを見る
3. click と CV の両方に出ているものを優先的に確認する
4. detail を見て、理由・証拠状態・関連行を確認する
5. 必要なら直近24時間の再取得をかけて欠損を補完する

## 14. 実装ファイルの見どころ

### ルール本体

- `backend/src/fraud_checker/suspicious.py`

### デフォルト値

- `backend/src/fraud_checker/config.py`

### DB または env から設定値を読み込む部分

- `backend/src/fraud_checker/services/settings.py`

### 日次 rollup を SQL でまとめる部分

- `backend/src/fraud_checker/repositories/reporting_read.py`

## 15. ひとことで言うと

いまの検知は、

> 同じ日・同じ IP・同じ UA が、多すぎる、広がりすぎる、短時間に集中しすぎる、CV 側でも同じように怪しい

ときに suspicious とみなす、説明しやすいルールベース検知です。
