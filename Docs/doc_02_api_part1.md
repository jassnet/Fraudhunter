## APIエンドポイント詳細

## APIエンドポイント詳細

### Access Log

**ファイルパス**: `src/v1/paths/access_log.yaml`

## search
### get
#### tags
- アクセスログ
**summary**: アクセスログ 取得（複数）

**description**: アクセスログを複数件取得します。初期ソートは、登録日時の降順です。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

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

広告情報のID

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

配列素材情報のID

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

**name**: date_y

**in**: query

**description**: 生成日時（年）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: date_m

**in**: query

**description**: 生成日時（月）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: date_d

**in**: query

**description**: 生成日時（日）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: date_unix

**in**: query

**description**: 生成日時

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
**$ref**: ../components/schemas/access_log.yaml#/search

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

## sum
### get
#### tags
- アクセスログ
**summary**: アクセスログ 取得（集計値）

**description**: アクセスログの集計値を取得します。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

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

**name**: promotion_item

**in**: query

**description**: 広告素材

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: media_space

**in**: query

**description**: 広告枠

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: media_space_item

**in**: query

**description**: 配信素材

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: ssp_space

**in**: query

**description**: SSP

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: date_y

**in**: query

**description**: 生成日時（年）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: date_m

**in**: query

**description**: 生成日時（月）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: date_d

**in**: query

**description**: 生成日時（日）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: date_unix

**in**: query

**description**: 生成日時

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
########## sum
**type**: object

########### properties
############ access
**type**: integer

**format**: int32

**description**: アクセス数

アクセス数の集計値

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

### Action Log

**ファイルパス**: `src/v1/paths/action_log.yaml`

## sum
### get
#### tags
- 成果報酬
**summary**: 成果報酬 取得（集計値）

**description**: 成果報酬の集計値を取得します。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

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

広告情報のID

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

**name**: state

**in**: query

**description**: 承認状態

0：未承認

1：承認

2：キャンセル

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
- 2
**name**: date_y

**in**: query

**description**: 生成日時（年）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: date_m

**in**: query

**description**: 生成日時（月）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: date_d

**in**: query

**description**: 生成日時（日）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: date_unix

**in**: query

**description**: 生成日時

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
########## sum
**type**: object

########### properties
############ action
**type**: integer

**format**: int32

**description**: 成果数

############ net_reward
**type**: integer

**format**: int32

**description**: 成果報酬額（ネット）

成果報酬額（ネット）の集計値

############ gross_reward
**type**: integer

**format**: int32

**description**: 成果報酬額（グロス）

成果報酬額（グロス）の集計値

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

### Action Log Raw

**ファイルパス**: `src/v1/paths/action_log_raw.yaml`

## search
### get
#### tags
- 成果報酬
**summary**: 成果報酬 取得（複数）

**description**: 成果報酬情報を複数件取得します。

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

**description**: 成果ID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: parent_user

**in**: query

**description**: 紹介者

紹介したアフィリエイター情報のID

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

広告情報のID

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

**name**: promotion_cost

**in**: query

**description**: 特別単価

特別単価情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: promotion_table

**in**: query

**description**: 報酬テーブル（pt）

報酬テーブル情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: check_log_raw

**in**: query

**description**: cid

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: plid

**in**: query

**description**: plid

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: action_type

**in**: query

**description**: 成果種別

normal：通常

manual：手動

promotion_goods：商品テーブル

promotion_table：報酬テーブル

promotion_cost：特別単価

call：電話経由

line：LINE友だち追加計測

**required**: False

**explode**: False

##### schema
**type**: string

###### enum
- normal
- manual
- promotion_goods
- promotion_table
- promotion_cost
- call
- line
**name**: subject

**in**: query

**description**: 成果内容

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: net_reward

**in**: query

**description**: 成果報酬額（ネット）

単位：円

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**maximum**: 99999999

**minimum**: 0

**name**: gross_reward

**in**: query

**description**: 成果報酬額（グロス）

単位：円

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**maximum**: 99999999

**minimum**: 0

**name**: tax_rate

**in**: query

**description**: 消費税率

単位：パーセント

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**maximum**: 100

**minimum**: 1

**name**: net_action_cost

**in**: query

**description**: 成果報酬単価（ネット）

定額（円）：0～99999999

定率（％）：0.00～999.99

**required**: False

**explode**: False

##### schema
**type**: number

**format**: float

**name**: net_action_cost_type

**in**: query

**description**: 成果報酬種別（ネット）（単位）

yen：円

per：％

**required**: False

**explode**: False

##### schema
**type**: string

###### enum
- yen
- per
**name**: gross_action_cost

**in**: query

**description**: 成果報酬単価（グロス）

定額（円）：0～99999999

定率（％）：0.00～999.99

**required**: False

**explode**: False

##### schema
**type**: number

**format**: float

**name**: gross_action_cost_type

**in**: query

**description**: 成果報酬種別（グロス）（単位）

yen：円

per：％

**required**: False

**explode**: False

##### schema
**type**: string

###### enum
- yen
- per
**name**: tier_rate

**in**: query

**description**: 2ティア率

単位：パーセント

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**maximum**: 100

**minimum**: 1

**name**: tier_rate3

**in**: query

**description**: 3ティア率

単位：パーセント

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**maximum**: 100

**minimum**: 1

**name**: tier_rate4

**in**: query

**description**: 4ティア率

単位：パーセント

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**maximum**: 100

**minimum**: 1

**name**: args

**in**: query

**description**: args（成果識別子）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: price

**in**: query

**description**: price（購入金額）

単位：円

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 0

**name**: did

**in**: query

**description**: did

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: tkp1

**in**: query

**description**: tkp1

**required**: False

**explode**: False

##### schema
**type**: string

**name**: tkp2

**in**: query

**description**: tkp2

**required**: False

**explode**: False

##### schema
**type**: string

**name**: tkp3

**in**: query

**description**: tkp3

**required**: False

**explode**: False

##### schema
**type**: string

**name**: pbid

**in**: query

**description**: pbid

**required**: False

**explode**: False

##### schema
**type**: string

**name**: kbp1

**in**: query

**description**: kbp1

**required**: False

**explode**: False

##### schema
**type**: string

**name**: kbp2

**in**: query

**description**: kbp2

**required**: False

**explode**: False

##### schema
**type**: string

**name**: kbp3

**in**: query

**description**: kbp3

**required**: False

**explode**: False

##### schema
**type**: string

**name**: pcp

**in**: query

**description**: pcp

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: state

**in**: query

**description**: 承認状態

0：未承認

1：承認

2：キャンセル

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
- 2
**name**: billing_flag

**in**: query

**description**: 請求状態

0：未処理

1：処理済み

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: payment_flag

**in**: query

**description**: 支払状態

0：未処理

1：処理済み

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: unique_id

**in**: query

**description**: ユニークID

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

**name**: memo

**in**: query

**description**: 管理者用メモ

**required**: False

**explode**: False

##### schema
**type**: string

**name**: click_unix

**in**: query

**description**: 広告クリック日時

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: regist_unix

**in**: query

**description**: 成果発生日時

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: apply_auto_unix

**in**: query

**description**: 承認予定日時

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: apply_unix

**in**: query

**description**: 成果確定日時

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
**$ref**: ../components/schemas/action_log_raw.yaml#/search

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
- 成果報酬
**summary**: 成果報酬 取得（1件）

**description**: 成果報酬情報を1件取得します。

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

**description**: 成果報酬のIDを入力してください。

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
**$ref**: ../components/schemas/action_log_raw.yaml#/info

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

### Advertiser

**ファイルパス**: `src/v1/paths/advertiser.yaml`

## search
### get
#### tags
- 広告主
**summary**: 広告主 取得（複数）

**description**: 広告主情報を複数件取得します。
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

**description**: 広告主のシステムID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**format**: uuid

**name**: company

**in**: query

**description**: 会社名

**required**: False

**explode**: True

##### schema
**type**: string

**maxLength**: 255

**example**: テスト株式会社

**name**: name

**in**: query

**description**: 氏名

##### schema
**type**: string

**maxLength**: 255

**example**: テスト株式会社

**name**: mail

**in**: query

**description**: メールアドレス

##### schema
**type**: string

**maxLength**: 255

**format**: email

**name**: tel

**in**: query

**description**: 電話番号

##### schema
**type**: string

**maxLength**: 32

**name**: add_num1

**in**: query

**description**: 郵便番号（上3桁）

##### schema
**type**: string

**maxLength**: 3

**name**: add_num2

**in**: query

**description**: 郵便番号（下4桁）

##### schema
**type**: string

**maxLength**: 4

**name**: add_text

**in**: query

**description**: 住所

##### schema
**type**: string

**maxLength**: 255

**name**: billing_state

**in**: query

**description**: 請求指定

0:システム設定参照

1：個別設定

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: billing_close_date

**in**: query

**description**: 集計期間の締め日

1～27：1～27日

0：月末

##### schema
**type**: integer

**minimum**: 0

**maximum**: 27

**format**: int32

**name**: billing_agg_date

**in**: query

**description**: 集計実行日

1～27：1～27日

0：月末

##### schema
**type**: integer

**minimum**: 0

**maximum**: 27

**format**: int32

**name**: billing_fix_month

**in**: query

**description**: 支払期日（月）

0: 当月

1: 翌月

2: 翌々月

##### schema
**type**: integer

###### enum
- 0
- 1
- 2
**format**: int32

**name**: billing_fix_date

**in**: query

**description**: 支払期日（日）

1～27：1～27日

0：月末

##### schema
**type**: integer

**minimum**: 0

**maximum**: 27

**format**: int32

**name**: user_state

**in**: query

**description**: アフィリエイター情報の表示

0: ID

1: アフィリエイター名

##### schema
**type**: integer

###### enum
- 0
- 1
**format**: int32

**name**: media_state

**in**: query

**description**: メディア情報の表示

0: ID

1: メディア名

2: すべて開示

##### schema
**type**: integer

###### enum
- 0
- 1
- 2
**format**: int32

**name**: search_state

**in**: query

**description**: 絞込み条件の表示

0: 非表示

1: 表示

##### schema
**type**: integer

###### enum
- 0
- 1
**format**: int32

**name**: referrer_state

**in**: query

**description**: リファラ情報の表示

0: 非表示

1: 表示

##### schema
**type**: integer

###### enum
- 0
- 1
**format**: int32

**name**: promotion_edit_state

**in**: query

**description**: 広告情報の編集・削除

0: 許可しない

1: 許可する

##### schema
**type**: integer

###### enum
- 0
- 1
**format**: int32

**name**: promotion_item_edit_state

**in**: query

**description**: 広告素材情報の編集・削除

0: 許可しない

1: 許可する

##### schema
**type**: integer

###### enum
- 0
- 1
**format**: int32

**name**: apply_edit_state

**in**: query

**description**: 提携申請ステータスの再編集

0: 許可しない

1: 許可する

##### schema
**type**: integer

###### enum
- 0
- 1
**format**: int32

**name**: action_edit_state

**in**: query

**description**: 成果ステータスの再編集

0: 許可しない

1: 許可する

##### schema
**type**: integer

###### enum
- 0
- 1
**format**: int32

**name**: container_operate_state

**in**: query

**description**: タグマネージャーの操作

0: 許可しない

1: 閲覧のみ許可する

2: 全操作許可する

##### schema
**type**: integer

###### enum
- 0
- 1
- 2
**format**: int32

**name**: state

**in**: query

**description**: アカウント状態

0: 未承認

1: 承認

2: 保留

3: 却下

4: 退会

##### schema
**type**: integer

###### enum
- 0
- 1
- 2
- 3
- 4
**format**: int32

**name**: mail_important_state

**in**: query

**description**: 重要メール配信

0: 受信しない

1: 受信する

##### schema
**type**: integer

###### enum
- 0
- 1
**format**: int32

**name**: mail_state

**in**: query

**description**: 通常メール配信

0: 受信しない

1: 受信する

##### schema
**type**: integer

###### enum
- 0
- 1
**format**: int32

**name**: action_mail_state

**in**: query

**description**: 成果報酬通知メール

0: 受信しない

1: 受信する

##### schema
**type**: integer

###### enum
- 0
- 1
**format**: int32

**name**: action_daily_mail_state

**in**: query

**description**: 成果報酬レポート（日別）メール

0: 受信しない

1: 受信する

##### schema
**type**: integer

###### enum
- 0
- 1
**format**: int32

**name**: memo

**in**: query

**description**: 管理者用メモ

##### schema
**type**: string

**name**: ipaddress

**in**: query

**description**: IPアドレス制限

##### schema
**type**: array

**name**: login_unix

**in**: query

**description**: 最終ログイン日時

unixtime形式

##### schema
**type**: integer

**format**: int32

**name**: edit_unix

**in**: query

**description**: 最終編集日時

unixtime形式

##### schema
**type**: integer

**format**: int32

**name**: regist_unix

**in**: query

**description**: 登録日時

unixtime形式

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
**$ref**: ../components/schemas/advertiser.yaml#/search

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
- 広告主
**summary**: 広告主 取得（1件）

**description**: 広告主情報を１件取得します。

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

**description**: 広告主のIDを入力してください。

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
**$ref**: ../components/schemas/advertiser.yaml#/info

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

### Banner Size

**ファイルパス**: `src/v1/paths/banner_size.yaml`

## search
