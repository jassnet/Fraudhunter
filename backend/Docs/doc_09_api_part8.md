## APIエンドポイント詳細

### get
#### tags
- 広告アイコン
**summary**: 広告アイコン 取得（複数）

**description**: 広告情報｜広告アイコンのマスター情報を複数件取得します。
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

**name**: icon_image

**in**: query

**description**: アイコン 画像ファイルの保存先URL

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
**$ref**: ../components/schemas/promotion_icon.yaml#/search

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
- 広告アイコン
**summary**: 広告アイコン 取得（1件）

**description**: 広告情報｜広告アイコンのマスター情報を1件取得します。

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

**description**: 広告アイコンのIDを入力してください。

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
**$ref**: ../components/schemas/promotion_icon.yaml#/info

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

### Promotion Item

**ファイルパス**: `src/v1/paths/promotion_item.yaml`

## search
### get
#### tags
- 広告素材
**summary**: 広告素材 取得（複数）

**description**: 広告素材情報を複数件取得します。初期ソートは、登録日時の降順です。

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

**name**: name

**in**: query

**description**: 広告素材名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: url_type

**in**: query

**description**: 広告遷移種別

via_system：システム経由方式

direct：直接リンク方式

**required**: False

**explode**: True

##### schema
**type**: array

**maxItems**: 2

###### items
**type**: string

**maxLength**: 64

####### enum
- via_system
- direct
**name**: banner_size

**in**: query

**description**: バナーサイズ

バナーサイズ情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: movie_size

**in**: query

**description**: フレームサイズ

フレームサイズ情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: ssp_template

**in**: query

**description**: テンプレート

テンプレート情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: ssp_template_type

**in**: query

**description**: 利用テンプレート

all：全て

fix：個別

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

###### enum
- all
- fix
**name**: ad_type

**in**: query

**description**: 広告素材種別

text：テキスト素材

image：バナー素材

movie：動画素材

template：テンプレート素材

parallel：リスティング素材

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

###### enum
- text
- image
- movie
- template
- parallel
**name**: item_label

**in**: query

**description**: 素材番号

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 16

**name**: ad_image

**in**: query

**description**: バナー

画像ファイルの保存先URL

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: ad_image_size_x

**in**: query

**description**: バナーサイズ（横）

1～9999

単位：px

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**maximum**: 9999

**name**: ad_image_size_y

**in**: query

**description**: バナーサイズ（縦）

1～9999

単位：px

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**maximum**: 9999

**name**: ad_movie

**in**: query

**description**: 動画

動画ファイルの保存先URL

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: ad_movie_image

**in**: query

**description**: サムネイル／ポスター

画像ファイルの保存先URL

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: ad_movie_size_x

**in**: query

**description**: フレームサイズ（横）

1～9999

単位：px

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**maximum**: 9999

**name**: ad_movie_size_y

**in**: query

**description**: フレームサイズ（縦）

1～9999

単位：px

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 1

**maximum**: 9999

**name**: ad_movie_time

**in**: query

**description**: 再生時間

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: ad_text

**in**: query

**description**: テキスト

テキスト素材の場合：テキスト

**required**: False

**explode**: False

##### schema
**type**: string

**name**: ad_sub_text1

**in**: query

**description**: サブテキスト１

**required**: False

**explode**: False

##### schema
**type**: string

**name**: ad_sub_text2

**in**: query

**description**: サブテキスト２

**required**: False

**explode**: False

##### schema
**type**: string

**name**: ad_sub_text3

**in**: query

**description**: サブテキスト３

**required**: False

**explode**: False

##### schema
**type**: string

**name**: url

**in**: query

**description**: 広告URL（システム経由）｜広告遷移URL

**required**: False

**explode**: False

##### schema
**type**: string

**name**: display_url

**in**: query

**description**: 広告確認用URL

**required**: False

**explode**: False

##### schema
**type**: string

**name**: smart_ios_url

**in**: query

**description**: 広告URL（システム経由）｜広告遷移URL（iOS）

**required**: False

**explode**: False

##### schema
**type**: string

**name**: smart_android_url

**in**: query

**description**: 広告URL（システム経由）｜広告遷移URL（Android）

**required**: False

**explode**: False

##### schema
**type**: string

**name**: action_name

**in**: query

**description**: 成果報酬表示名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: cid_flag

**in**: query

**description**: 広告URL（システム経由）｜成果認証用ID自動付与設定（cid）

0：付与しない

1：「cid=値」で付与する

2：cidの値のみ付与する

3：「[cid]」を値で置換する

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
**name**: p_flag

**in**: query

**description**: 広告URL（システム経由）｜広告ID自動付与設定（p）

0：付与しない

1：「p=値」で付与する

2：pの値のみ付与する

3：「[p]」を値で置換する

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
**name**: mid_flag

**in**: query

**description**: 広告URL（システム経由）｜メディアID自動付与設定（mid）

0：付与しない

1：「mid=値」で付与する

2：midの値のみ付与する

3：「[mid]」を値で置換する

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
**name**: link_type

**in**: query

**description**: 広告URL（システム経由）｜リファラ取得設定

0：取得する

1：取得しない

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: item_link_state

**in**: query

**description**: 商品リンク設定

0：無効

1：有効（URL照合なし）

2：有効（URL照合あり）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
- 2
**name**: item_link_url

**in**: query

**description**: 商品リンク照合用URL

**required**: False

**explode**: False

##### schema
**type**: string

**name**: direct_url

**in**: query

**description**: 広告URL（直接リンク）｜広告遷移URL

**required**: False

**explode**: False

##### schema
**type**: string

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
**$ref**: ../components/schemas/promotion_item.yaml#/search

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
- 広告素材
**summary**: 広告素材 取得（1件）

**description**: 広告素材情報を1件取得します。

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

**description**: 広告素材のIDを入力してください。

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
**$ref**: ../components/schemas/promotion_item.yaml#/info

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
- 広告素材
**summary**: 広告素材登録

**description**: 広告素材の登録を行います。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

#### requestBody
**$ref**: ../components/request_bodies/promotion_item.yaml#/regist

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/promotion_item.yaml#/info

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
- 広告素材
**summary**: 広告素材編集

**description**: 広告素材の編集を行います。

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

**description**: 広告素材のIDを入力してください。

**required**: True

**explode**: False

##### schema
**type**: string

**format**: uuid

#### requestBody
**$ref**: ../components/request_bodies/promotion_item.yaml#/edit

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/promotion_item.yaml#/info

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

### Promotion Table

**ファイルパス**: `src/v1/paths/promotion_table.yaml`

## search
### get
#### tags
- 報酬テーブル
**summary**: 報酬テーブル 取得（複数）

**description**: 広告詳細｜報酬テーブル 情報を複数件取得します。
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

**name**: pt_id

**in**: query

**description**: 報酬テーブルID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: name

**in**: query

**description**: 報酬テーブル名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: net_action_cost

**in**: query

**description**: 成果報酬単価（ネット）

定額（円）：0～99999999

定率（％）：0.00～999.99

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 0

**maximum**: 99999999

**name**: net_action_cost_type

**in**: query

**description**: 成果報酬単価（ネット）（単位）

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
**name**: gross_action_cost

**in**: query

**description**: 成果報酬単価（グロス）

定額（円）：0～99999999

定率（％）：0.00～999.99

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 0

**maximum**: 99999999

**name**: gross_action_cost_type

**in**: query

**description**: 成果報酬単価（グロス）（単位）

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
**name**: state

**in**: query

**description**: ステータス

0：無効

1：有効

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
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
**$ref**: ../components/schemas/promotion_table.yaml#/search

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
- 報酬テーブル
**summary**: 報酬テーブル 取得（1件）

**description**: 広告詳細｜報酬テーブルの情報を1件取得します。

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

**description**: 報酬テーブルのIDを入力してください。

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
**$ref**: ../components/schemas/promotion_table.yaml#/info

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

### Ssp Space

**ファイルパス**: `src/v1/paths/ssp_space.yaml`

## search
### get
#### tags
- SSP
**summary**: SSP 取得（複数）

**description**: SSP情報を複数件取得します。
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

**name**: name

**in**: query

**description**: SSP名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: ssp_space_type

**in**: query

**description**: SSP種別

text：テキスト

image：バナー

template：テンプレート

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

###### enum
- text
- image
- template
**name**: ssp_template

**in**: query

**description**: SSPテンプレート

SSPテンプレート情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: ssp_template_row

**in**: query

**description**: 広告表示数

SSP枠に表示する広告数

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: banner_size

**in**: query

**description**: バナーサイズ

バナーサイズ情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

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
**$ref**: ../components/schemas/ssp_space.yaml#/search

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
- SSP
**summary**: SSP 取得（１件）

**description**: SSP情報を１件取得します。

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

**description**: SSP 取得（１件）のIDを入力してください。

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
**$ref**: ../components/schemas/ssp_space.yaml#/info

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
