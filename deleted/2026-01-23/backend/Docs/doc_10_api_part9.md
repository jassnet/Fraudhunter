## APIエンドポイント詳細

### System

**ファイルパス**: `src/v1/paths/system.yaml`

## info
### get
#### tags
- システム情報
**summary**: システム情報 取得（1件）

**description**: システム情報を1件取得します。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/system.yaml#/info

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

### Track Log

**ファイルパス**: `src/v1/paths/track_log.yaml`

## search
### get
#### tags
- トラッキングログ
**summary**: トラッキングログ取得（複数）

**description**: トラッキングログ情報を複数件取得します。

初期ソートは、登録日時の降順です。

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

アフィリエイター情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: media

**in**: query

**description**: メディア

メディア情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: advertiser

**in**: query

**description**: 広告主

広告主情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: promotion

**in**: query

**description**: 広告

広告情報のID（ｐパラメータの値）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: promotion_item

**in**: query

**description**: 広告素材

広告素材情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: media_space

**in**: query

**description**: 広告枠

広告枠情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: media_space_item

**in**: query

**description**: 配信素材

配信素材情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: ssp_space

**in**: query

**description**: SSP

SSP情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: action_log_raw

**in**: query

**description**: 成果

成果情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: auth_type

**in**: query

**description**: 認証方式

cid_get：cid（GET）認証

cid_cookie：cid（Cookie）認証

plid_get：plid（GET）認証

plid_cookie：plid（Cookie）認証

ip_ua：IP･UA認証

mid：mid認証

did：did認証

error：エラー

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

###### enum
- cid_get
- cid_cookie
- plid_get
- plid_cookie
- ip_ua
- mid
- did
- error
**name**: auth_get_type

**in**: query

**description**: GET認証の取得方法

php：Cookie（PHP）経由

js：Cookie（JS）経由

ls：LocalStorage経由

other：その他

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

###### enum
- php
- js
- ls
- other
**name**: track_url

**in**: query

**description**: トラッキングURL

**required**: False

**explode**: False

##### schema
**type**: string

**name**: track_cid

**in**: query

**description**: cid

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_plid

**in**: query

**description**: plid

**required**: False

**explode**: False

##### schema
**type**: string

**name**: track_mid

**in**: query

**description**: mid

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_pass

**in**: query

**description**: t（成果認証パスワード）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_args

**in**: query

**description**: args（成果識別子）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_price

**in**: query

**description**: price（購入金額）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_pt

**in**: query

**description**: pt（報酬テーブル）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_pg

**in**: query

**description**: pg（商品テーブル）

**required**: False

**explode**: False

##### schema
**type**: string

**name**: track_did

**in**: query

**description**: did

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: track_state

**in**: query

**description**: state

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: track_tkp1

**in**: query

**description**: tkp1

**required**: False

**explode**: False

##### schema
**type**: string

**name**: track_tkp2

**in**: query

**description**: tkp2

**required**: False

**explode**: False

##### schema
**type**: string

**name**: track_tkp3

**in**: query

**description**: tkp3

**required**: False

**explode**: False

##### schema
**type**: string

**name**: track_cap

**in**: query

**description**: cap

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: referrer

**in**: query

**description**: リファラ

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
**type**: string

**maxLength**: 15

**name**: useragent

**in**: query

**description**: ユーザーエージェント

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: state

**in**: query

**description**: トラッキングコード

<a href="https://blog.affilicode.jp/article/20123" target="blank">マニュアル参照</a>

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: regist_unix

**in**: query

**description**: トラッキング日時

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
**$ref**: ../components/schemas/track_log.yaml#/search

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
- トラッキングログ
**summary**: トラッキングログ取得（1件）

**description**: トラッキングログ情報を複数件取得します。

初期ソートは、登録日時の降順です。

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

**description**: トラッキングログのIDを入力してください。

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
**$ref**: ../components/schemas/track_log.yaml#/info

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

### User

**ファイルパス**: `src/v1/paths/user.yaml`

## search
### get
#### tags
- アフィリエイター
**summary**: アフィリエイター 取得（複数）

**description**: アフィリエイター情報を複数件取得します。

初期ソートは、登録日時の降順です。

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

**name**: parent_user

**in**: query

**description**: 紹介者

紹介者情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: company

**in**: query

**description**: 会社名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: name

**in**: query

**description**: 氏名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: mail

**in**: query

**description**: メールアドレス

**required**: False

**explode**: False

##### schema
**type**: string

**format**: email

**maxLength**: 255

**name**: tel

**in**: query

**description**: 電話番号

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: add_num1

**in**: query

**description**: 郵便番号（上3桁）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 3

**name**: add_num2

**in**: query

**description**: 郵便番号（下4桁）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 4

**name**: add_text

**in**: query

**description**: 住所

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: invoice_license_num

**in**: query

**description**: 適格請求書発行事業者の登録番号

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 14

**name**: bank_name

**in**: query

**description**: 金融機関名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 64

**name**: bank_code

**in**: query

**description**: 金融機関コード

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 4

**name**: bank_branch_name

**in**: query

**description**: 支店名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 64

**name**: bank_branch_code

**in**: query

**description**: 支店コード

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 3

**name**: bank_u_type

**in**: query

**description**: 口座種別

ordinary：普通

current：当座

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 16

###### enum
- ordinary
- current
**name**: bank_u_num

**in**: query

**description**: 口座番号

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 16

**name**: bank_u_name

**in**: query

**description**: 口座名義

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 64

**name**: payment_exchange_type

**in**: query

**description**: 支払方式

fix：毎月方式

over：繰越方式

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

###### enum
- fix
- over
**name**: payment_exchange_state

**in**: query

**description**: 支払申請

0：申請しない

1：申請する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: payment_state

**in**: query

**description**: 支払指定

0：システム設定参照

1：個別設定

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: payment_close_date

**in**: query

**description**: 集計期間の締め日

1～27：1～27日

0：月末

**required**: False

**explode**: False

##### schema
**type**: integer

**minimum**: 0

**maximum**: 27

**name**: payment_agg_date

**in**: query

**description**: 集計実行日

1～27：1～27日

0：月末

**required**: False

**explode**: False

##### schema
**type**: integer

**minimum**: 0

**maximum**: 27

**name**: payment_fix_month

**in**: query

**description**: 振込予定日（月）

0：当月

1：翌月

2：翌々月

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
- 2
**name**: payment_fix_date

**in**: query

**description**: 振込予定日（日）

1～27：1～27日

0：月末

**required**: False

**explode**: False

##### schema
**type**: integer

**minimum**: 0

**maximum**: 27

**name**: payment_exchange_fee_cost

**in**: query

**description**: 振込手数料

0～2147483647 　　単位：円

**required**: False

**explode**: False

##### schema
**type**: integer

**minimum**: 0

**name**: action_col_state

**in**: query

**description**: 成果項目の表示設定

0：システム設定参照

1：個別設定

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: action_col_display

**in**: query

**description**: 成果項目の表示内容

click_unix：広告クリック日時

regist_row：発生成果数

regist_reward：発生成果額

regist_unix：成果発生日時

apply_unix：成果確定日時

referrer：リファラ

link_view：広告URLパラメータ

track_view：トラッキングパラメータ

**required**: False

**explode**: False

##### schema
**type**: array

###### enum
- click_unix
- regist_row
- regist_reward
- regist_unix
- apply_unix
- referrer
- link_view
- track_view
**name**: state

**in**: query

**description**: アカウント状態

0：未承認

1：承認

2：保留

3：却下

4：退会

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
- 2
- 3
- 4
**example**: 0

**name**: mail_important_state

**in**: query

**description**: 重要メール配信

0：受信しない

1：受信する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: mail_state

**in**: query

**description**: 通常メール配信

0：受信しない

1：受信する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: action_mail_state

**in**: query

**description**: 成果報酬通知メール

0：受信しない

1：確定成果のみ受信（承認）

2：初回発生時のみ受信（未承認・承認）

3：全て受信（未承認・承認・キャンセル）

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
- 2
- 3
**name**: action_daily_mail_state

**in**: query

**description**: 成果報酬レポート（日別）メール

0：受信しない

1：受信する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: user_group

**in**: query

**description**: グループ

グループ情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: memo

**in**: query

**description**: 管理者用メモ

**required**: False

**explode**: False

##### schema
**type**: string

**name**: ipaddress

**in**: query

**description**: IPアドレス制限

**required**: False

**explode**: False

##### schema
**type**: array

**name**: login_unix

**in**: query

**description**: 最終ログイン日時

Unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**name**: edit_unix

**in**: query

**description**: 最終編集日時

Unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**name**: regist_unix

**in**: query

**description**: 登録日時

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

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
**$ref**: ../components/schemas/user.yaml#/search

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
- アフィリエイター
**summary**: アフィリエイター 取得（1件）

**description**: アフィリエイター情報を1件取得します。

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

**description**: アフィリエイターのIDを入力してください。

**required**: True

**explode**: False

##### schema
**type**: string

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/user.yaml#/info

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
- アフィリエイター
**summary**: アフィリエイター登録

**description**: アフィリエイターの登録を行います。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

#### requestBody
**$ref**: ../components/request_bodies/user.yaml#/regist

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/user.yaml#/info

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
- アフィリエイター
**summary**: アフィリエイター編集

**description**: アフィリエイターの編集を行います。

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

**description**: アフィリエイターのIDを入力してください。

**required**: True

**explode**: False

##### schema
**type**: string

#### requestBody
**$ref**: ../components/request_bodies/user.yaml#/edit

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/user.yaml#/info

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

### User Group

**ファイルパス**: `src/v1/paths/user_group.yaml`

## search
### get
#### tags
- グループ
**summary**: グループ情報取得（複数）

**description**: アフィリエイター情報｜グループのマスター情報を複数件取得します。
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

**description**: グループのID

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

-99～999

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
**$ref**: ../components/schemas/user_group.yaml#/search

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
- グループ
**summary**: グループ 取得（1件）

**description**: アフィリエイター情報｜グループのマスター情報を1件取得します。

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

**description**: グループのIDを入力してください。

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
**$ref**: ../components/schemas/user_group.yaml#/info

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
