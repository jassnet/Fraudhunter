## APIエンドポイント詳細

### Promotion

**ファイルパス**: `src/v1/paths/promotion.yaml`

## search
### get
#### tags
- 広告
**summary**: 広告 取得（複数）

**description**: 広告情報を複数件取得します。
初期ソートは、掲載更新日の降順（第一ソート）、登録日時の降順（第二ソート）です。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

**name**: id

**in**: query

**description**: ID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: advertiser

**in**: query

**description**: 広告主　広告主情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: name

**in**: query

**description**: 広告名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: promotion_category

**in**: query

**description**: 広告カテゴリー

広告カテゴリー情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: promotion_device

**in**: query

**description**: 対応デバイス

対応デバイス情報のID

**required**: False

**explode**: False

##### schema
**type**: array

**maxLength**: 255

**name**: promotion_type

**in**: query

**description**: 広告種別

click：クリック保証広告

action：成果保証広告

**required**: False

**explode**: False

##### schema
**type**: array

**maxLength**: 64

###### enum
- click
- action
**name**: net_click_cost

**in**: query

**description**: クリック単価（ネット）

単位：円

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**maximum**: 99999999

**name**: net_action_cost

**in**: query

**description**: 成果報酬単価（ネット）

定額（円）：0～99999999

低率（％）：0.00～999.99

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: float

**maximum**: 99999999

**name**: net_action_cost_type

**in**: query

**description**: 成果報酬単価（ネット）の単位

yen：円

per：％

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 16

###### enum
- yen
- per
**name**: gross_click_cost

**in**: query

**description**: クリック単価（グロス）

0～99999999

単位：円

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**maximum**: 99999999

**name**: gross_action_cost

**in**: query

**description**: 成果報酬単価（グロス）

定額（円）：0～99999999

定率（％）：0.00～999.99

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: float

**maximum**: 99999999

**name**: gross_action_cost_type

**in**: query

**description**: 成果報酬単価（グロス）の単位

yen：円

per：％

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 16

###### enum
- yen
- per
**name**: click_state

**in**: query

**description**: 連続クリック設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: click_time

**in**: query

**description**: 連続クリックの有効期限

単位：秒

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: action_name

**in**: query

**description**: 成果報酬表示名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: action_cost_round

**in**: query

**description**: 丸め誤差調整

0：四捨五入

1：切り捨て

2：切り上げ

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
- 2
**name**: action_time

**in**: query

**description**: 広告クリックから成果発生までの有効期間

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: action_time_type

**in**: query

**description**: 広告クリックから成果発生までの有効期間の単位

86400：日

3600：時間

60：分

1：秒

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 86400
- 3600
- 60
- 1
**name**: action_ip_auth

**in**: query

**description**: IP･UAによる成果認証

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: action_cid_del

**in**: query

**description**: 成果発生時のセッション設定

0：無効にしない

1：無効にする

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: action_apply_state

**in**: query

**description**: 成果承認設定

0：手動承認

1：自動承認

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: action_apply_auto_state

**in**: query

**description**: 成果承認の期限設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: action_apply_auto_day

**in**: query

**description**: 成果自動承認期間（日）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**maximum**: 999

**name**: action_apply_auto_hour

**in**: query

**description**: 成果自動承認期間（時）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 0

**maximum**: 23

**name**: action_double_state

**in**: query

**description**: 成果重複チェック

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: action_double_type

**in**: query

**description**: 重複チェック方式

args：argsチェック

ip：IP･UAチェック

**required**: False

**explode**: False

##### schema
**type**: array

###### enum
- args
- ip
**name**: action_double_time

**in**: query

**description**: 重複とする期間

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 0

**name**: action_double_time_type

**in**: query

**description**: 重複とする期間の単位

86400：日

3600：時間

60：分

1：秒

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 86400
- 3600
- 60
- 1
**name**: check_pass

**in**: query

**description**: 成果認証パスワード

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: limit_type

**in**: query

**description**: 掲載制御条件設定

click：クリック件数上限

action：成果件数上限

amount：成果予算上限

date：掲載期限

**required**: False

**explode**: False

##### schema
**type**: array

**maxLength**: 64

###### enum
- click
- action
- amount
- date
**name**: limit_flag

**in**: query

**description**: 掲載制御状態

0：掲載未終了

1：掲載終了

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: limit_view_state

**in**: query

**description**: 掲載制御時の取り下げ設定

0：掲載を続ける

1：取り下げ

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: limit_notice_mail

**in**: query

**description**: 成果予算予告メール設定

0：通知しない

1：通知する

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: limit_click

**in**: query

**description**: クリック件数上限

単位：件

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 0

**name**: limit_action

**in**: query

**description**: 成果件数上限

単位：件

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**name**: limit_amount_type

**in**: query

**description**: 成果予算期間設定

total：全期間

monthly：月単位

daily：日単位

**required**: False

**explode**: False

##### schema
**type**: array

**maxLength**: 32

###### enum
- total
- monthly
- daily
**name**: total_limit_amount

**in**: query

**description**: 成果全期間上限の設定金額

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**name**: total_notice_rate

**in**: query

**description**: 成果全期間上限の通知割合

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**maximum**: 99

**name**: monthly_limit_amount

**in**: query

**description**: 成果月単位上限の設定金額

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**name**: monthly_notice_rate

**in**: query

**description**: 成果月単位上限の通知割合

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**maximum**: 99

**name**: daily_limit_amount

**in**: query

**description**: 成果日単位上限の設定金額

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**name**: daily_notice_rate

**in**: query

**description**: 成果日単位上限の通知割合

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**maximum**: 99

**name**: limit_date_unix

**in**: query

**description**: 掲載期限

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: limit_url

**in**: query

**description**: 稼働停止時のリダイレクト先

**required**: False

**explode**: False

##### schema
**type**: string

**name**: suspend_url

**in**: query

**description**: 稼働制限時のリダイレクト先

**required**: False

**explode**: False

##### schema
**type**: string

**name**: display_image

**in**: query

**description**: サムネイル

画像URL

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: display_url

**in**: query

**description**: 広告サイト確認用URL

**required**: False

**explode**: False

##### schema
**type**: string

**name**: display_title

**in**: query

**description**: キャッチコピー

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: display_pr

**in**: query

**description**: PR文

**required**: False

**explode**: False

##### schema
**type**: string

**name**: display_action

**in**: query

**description**: 成果条件

**required**: False

**explode**: False

##### schema
**type**: string

**name**: display_denial

**in**: query

**description**: 否認条件

**required**: False

**explode**: False

##### schema
**type**: string

**name**: display_ban

**in**: query

**description**: 禁止事項

**required**: False

**explode**: False

##### schema
**type**: string

**name**: display_remarks

**in**: query

**description**: 備考

**required**: False

**explode**: False

##### schema
**type**: string

**name**: display_date_unix

**in**: query

**description**: 掲載更新日

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: promotion_icon

**in**: query

**description**: アイコン表示

広告アイコン情報のID

**required**: False

**explode**: False

##### schema
**type**: array

**name**: state

**in**: query

**description**: 掲載ステータス

0：未承認

1：承認

2：保留

3：却下

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
- 2
- 3
**name**: change_state

**in**: query

**description**: 公開予約設定

公開設定：非公開時

0：予約しない

1：予約する

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: change_date_unix

**in**: query

**description**: 公開日時

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: opens

**in**: query

**description**: 公開設定

0：非公開

1：公開

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: opens_mail_state

**in**: query

**description**: 非公開通知メール設定

0：送信しない

1：送信する

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: apply_state

**in**: query

**description**: 提携承認設定

0：手動承認

1：自動承認

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: given_state

**in**: query

**description**: 限定公開設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: did_state

**in**: query

**description**: 成果ステータス変更設定

0：許可しない

1：許可する

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: state_val0

**in**: query

**description**: 成果ステータス変換（未承認）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: state_val1

**in**: query

**description**: 成果ステータス変換（承認）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: state_val2

**in**: query

**description**: 成果ステータス変換（キャンセル）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_cid

**in**: query

**description**: トラッキングパラメータ変換（cid）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_plid

**in**: query

**description**: トラッキングパラメータ変換（plid）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_mid

**in**: query

**description**: トラッキングパラメータ変換（mid）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_args

**in**: query

**description**: トラッキングパラメータ変換（args）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_price

**in**: query

**description**: トラッキングパラメータ変換（price）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_pt

**in**: query

**description**: トラッキングパラメータ変換（pt）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_pg

**in**: query

**description**: トラッキングパラメータ変換（pg）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_did

**in**: query

**description**: トラッキングパラメータ変換（did）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_state

**in**: query

**description**: トラッキングパラメータ変換（state）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_tkp1

**in**: query

**description**: トラッキングパラメータ変換（tkp1）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_tkp2

**in**: query

**description**: トラッキングパラメータ変換（tkp2）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_tkp3

**in**: query

**description**: トラッキングパラメータ変換（tkp3）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_cap

**in**: query

**description**: トラッキングパラメータ変換（cap）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_return

**in**: query

**description**: トラッキング時レスポンス設定

txt：テキスト値（OK・NG）

img：imgタグ

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 16

###### enum
- txt
- img
**name**: track_return_ok

**in**: query

**description**: トラッキング時レスポンス設定（テキスト値[OK]）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 64

**name**: track_return_ng

**in**: query

**description**: トラッキング時レスポンス設定（テキスト値[NG]）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 64

**name**: fb_cv_state

**in**: query

**description**: Facebook広告CV連携設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: fb_cv_pixel

**in**: query

**description**: ピクセルID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 64

**name**: fb_cv_token

**in**: query

**description**: アクセストークン

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: fb_cv_test

**in**: query

**description**: テストコード

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: fb_cv_name

**in**: query

**description**: イベント名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: fb_cv_url

**in**: query

**description**: イベントURL

**required**: False

**explode**: False

##### schema
**type**: string

**name**: line_follow_cv_state

**in**: query

**description**: LINE友だち追加計測設定

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: line_client_id

**in**: query

**description**: チャネルID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: line_client_secret

**in**: query

**description**: チャネルシークレット

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: line_bot_basic

**in**: query

**description**: ボットのベーシックID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: line_unfollow_state

**in**: query

**description**: 友だち解除時の成果自動キャンセル設定

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: line_unfollow_time

**in**: query

**description**: 成果自動キャンセル期間

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: line_unfollow_time_type

**in**: query

**description**: 成果自動キャンセル期間の単位

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: line_notify_url

**in**: query

**description**: スルー通知先URL

**required**: False

**explode**: False

##### schema
**type**: string

**name**: tier_state

**in**: query

**description**: 広告別ティア設定

0：システム設定参照

1：個別設定

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: tier_rate

**in**: query

**description**: 2ティア率

1～100

単位：パーセント

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**maximum**: 100

**name**: tier_rate3

**in**: query

**description**: 3ティア率

1～100

単位：パーセント

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**maximum**: 100

**name**: tier_rate4

**in**: query

**description**: 4ティア率

1～100

単位：パーセント

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**maximum**: 100

**name**: memo

**in**: query

**description**: メモ

**required**: False

**explode**: False

##### schema
**type**: string

**name**: admin_memo

**in**: query

**description**: 管理者用メモ

**required**: False

**explode**: False

##### schema
**type**: string

**name**: ipaddress

**in**: query

**description**: IPアドレス

**required**: False

**explode**: False

##### schema
**type**: array

**name**: ip_allow

**in**: query

**description**: IPアドレス制限設定

0：拒否する

1：許可する

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: edit_unix

**in**: query

**description**: 最終編集日時

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: regist_unix

**in**: query

**description**: 登録日時

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## header
**$ref**: ../components/schemas/header.yaml

########## records
**$ref**: ../components/schemas/promotion.yaml#/search

##### 400
**description**: 不正リクエスト(パラメータ不正等)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/400

##### 401
**description**: 認証失敗

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/401

##### 403
**description**: アクセス禁止

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/403

##### 404
**description**: 未検出(API機能の無効)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/404

##### 405
**description**: メソッドの不許可

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/405

## info
### get
#### tags
- 広告
**summary**: 広告 取得（1件）

**description**: 広告情報を1件取得します。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

**name**: id

**in**: query

**description**: 広告のIDを入力してください。

**required**: True

**explode**: False

##### schema
**type**: string

**format**: uuid

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/promotion.yaml#/info

##### 400
**description**: 不正リクエスト(パラメータ不正等)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/400

##### 401
**description**: 認証失敗

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/401

##### 403
**description**: アクセス禁止

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/403

##### 404
**description**: 未検出(API機能の無効)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/404

##### 405
**description**: メソッドの不許可

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/405

## regist
### post
#### tags
- 広告
**summary**: 広告登録

**description**: 広告の登録を行います。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

#### requestBody
**$ref**: ../components/request_bodies/promotion.yaml#/regist

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/promotion.yaml#/info

##### 400
**description**: 不正リクエスト(パラメータ不正等)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/400

##### 401
**description**: 認証失敗

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/401

##### 403
**description**: アクセス禁止

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/403

##### 404
**description**: 未検出(API機能の無効)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/404

##### 405
**description**: メソッドの不許可

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/405

## edit
### put
#### tags
- 広告
**summary**: 広告編集

**description**: 広告の編集を行います。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

**name**: id

**in**: query

**description**: 広告のIDを入力してください。

**required**: True

**explode**: False

##### schema
**type**: string

**format**: uuid

#### requestBody
**$ref**: ../components/request_bodies/promotion.yaml#/edit

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/promotion.yaml#/info

##### 400
**description**: 不正リクエスト(パラメータ不正等)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/400

##### 401
**description**: 認証失敗

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/401

##### 403
**description**: アクセス禁止

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/403

##### 404
**description**: 未検出(API機能の無効)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/404

##### 405
**description**: メソッドの不許可

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/405


---

### Promotion Apply

**ファイルパス**: `src/v1/paths/promotion_apply.yaml`

## search
### get
#### tags
- 提携申請
**summary**: 提携申請 取得（複数）

**description**: 広告詳細｜提携申請情報を複数件取得します。
初期ソートは、IDの降順です。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

**name**: id

**in**: query

**description**: ID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: user

**in**: query

**description**: アフィリエイター

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: media

**in**: query

**description**: メディア

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: advertiser

**in**: query

**description**: 広告主

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: promotion

**in**: query

**description**: 広告

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: state

**in**: query

**description**: 承認状態

0：未承認

1：承認

2：保留

3：却下

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
- 2
- 3
#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## header
**$ref**: ../components/schemas/header.yaml

########## records
**$ref**: ../components/schemas/promotion_apply.yaml#/search

##### 400
**description**: 不正リクエスト(パラメータ不正等)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/400

##### 401
**description**: 認証失敗

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/401

##### 403
**description**: アクセス禁止

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/403

##### 404
**description**: 未検出(API機能の無効)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/404

##### 405
**description**: メソッドの不許可

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/405

## info
### get
#### tags
- 提携申請
**summary**: 提携申請 取得（1件）

**description**: 広告詳細｜提携申請の情報を1件取得します。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

**name**: id

**in**: query

**description**: 提携申請のIDを入力してください。

**required**: True

**explode**: False

##### schema
**type**: string

**format**: uuid

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/promotion_apply.yaml#/info

##### 400
**description**: 不正リクエスト(パラメータ不正等)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/400

##### 401
**description**: 認証失敗

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/401

##### 403
**description**: アクセス禁止

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/403

##### 404
**description**: 未検出(API機能の無効)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/404

##### 405
**description**: メソッドの不許可

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/405

## regist
### post
#### tags
- 提携申請
**summary**: 提携申請登録

**description**: 提携申請の登録を行います。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

#### requestBody
**$ref**: ../components/request_bodies/promotion_apply.yaml#/regist

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/promotion_apply.yaml#/regist

##### 400
**description**: 不正リクエスト(パラメータ不正等)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/400

##### 401
**description**: 認証失敗

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/401

##### 403
**description**: アクセス禁止

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/403

##### 404
**description**: 未検出(API機能の無効)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/404

##### 405
**description**: メソッドの不許可

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/405

## edit
### put
#### tags
- 提携申請
**summary**: 提携申請編集

**description**: 提携申請の編集を行います。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

#### requestBody
**$ref**: ../components/request_bodies/promotion_apply.yaml#/edit

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/promotion_apply.yaml#/info

##### 400
**description**: 不正リクエスト(パラメータ不正等)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/400

##### 401
**description**: 認証失敗

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/401

##### 403
**description**: アクセス禁止

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/403

##### 404
**description**: 未検出(API機能の無効)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/404

##### 405
**description**: メソッドの不許可

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/405


---

### Promotion Category

**ファイルパス**: `src/v1/paths/promotion_category.yaml`

## search
### get
#### tags
- 広告カテゴリー
**summary**: 広告カテゴリー取得（複数）

**description**: 広告情報｜広告カテゴリーのマスター情報を複数件取得します。
初期ソートは、並び順の昇順です。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

**name**: id

**in**: query

**description**: ID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: name

**in**: query

**description**: 項目名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: wait

**in**: query

**description**: 並び順

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: -99

**maximum**: 999

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## header
**$ref**: ../components/schemas/header.yaml

########## records
**$ref**: ../components/schemas/promotion_category.yaml#/search

##### 400
**description**: 不正リクエスト(パラメータ不正等)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/400

##### 401
**description**: 認証失敗

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/401

##### 403
**description**: アクセス禁止

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/403

##### 404
**description**: 未検出(API機能の無効)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/404

##### 405
**description**: メソッドの不許可

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/405

## info
### get
#### tags
- 広告カテゴリー
**summary**: 広告カテゴリー 取得（1件）

**description**: 広告情報｜広告カテゴリーのマスター情報を1件取得します。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

**name**: id

**in**: query

**description**: 広告カテゴリーのIDを入力してください。

**required**: True

**explode**: False

##### schema
**type**: string

**format**: uuid

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/promotion_category.yaml#/info

##### 400
**description**: 不正リクエスト(パラメータ不正等)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/400

##### 401
**description**: 認証失敗

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/401

##### 403
**description**: アクセス禁止

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/403

##### 404
**description**: 未検出(API機能の無効)

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/404

##### 405
**description**: メソッドの不許可

###### content
####### application/json
######## schema
**$ref**: ../components/schemas/error.yaml#/405


---
