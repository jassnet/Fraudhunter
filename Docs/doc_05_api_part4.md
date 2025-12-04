## APIエンドポイント詳細

### Media Space Item

**ファイルパス**: `src/v1/paths/media_space_item.yaml`

## search
### get
#### tags
- 配信素材
**summary**: 配信素材 取得（複数）

**description**: 配信素材情報を複数件取得します。
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

**name**: name

**in**: query

**description**: 配信素材名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

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

**description**: メディアID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: media_space

**in**: query

**description**: 広告枠ID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: media_space_trigger

**in**: query

**description**: 出力条件設定：条件ありの場合

対象配信条件ID

配信条件のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: ssp_space

**in**: query

**description**: 素材種別がSSPの場合

SSP

SSP情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: promotion

**in**: query

**description**: 素材種別が広告素材の場合

対象広告

対象広告のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: promotion_item

**in**: query

**description**: 素材種別が広告素材の場合

広告素材

対象広告素材のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: item_type

**in**: query

**description**: 素材種別

promotion_item：広告素材

ssp：SSP

custom：カスタム（直接記述）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

###### enum
- promotion_item
- ssp
- custom
**name**: item_custom_data

**in**: query

**description**: 素材種別がカスタムの場合

カスタム（直接記述）

出力コードの内容

**required**: False

**explode**: False

##### schema
**type**: string

**name**: condition_state

**in**: query

**description**: 出力条件設定

0：無条件

1：条件あり

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
**name**: begin_date_unix

**in**: query

**description**: 配信開始日

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: end_date_unix

**in**: query

**description**: 配信終了日

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

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
**$ref**: ../components/schemas/media_space_item.yaml#/search

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
- 配信素材
**summary**: 配信素材 取得（1件）

**description**: 配信素材を1件取得します。

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

**description**: 配信素材のIDを入力してください。

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
**$ref**: ../components/schemas/media_space_item.yaml#/info

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
- 配信素材
**summary**: 配信素材登録

**description**: 配信素材の登録を行います。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

#### requestBody
**$ref**: ../components/request_bodies/media_space_item.yaml#/regist

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/media_space_item.yaml#/info

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

### Media Space Trigger

**ファイルパス**: `src/v1/paths/media_space_trigger.yaml`

## search
### get
#### tags
- 配信条件
**summary**: 配信条件 取得（複数）

**description**: 広告枠の配信条件情報を複数件取得します。
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

**name**: name

**in**: query

**description**: 配信条件名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: user

**in**: query

**description**: 対象アフィリエイターID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: condition_category

**in**: query

**description**: 配信条件設定

device：端末

week：曜日

time：時間

keyword：キーワード

**required**: False

**explode**: False

##### schema
**type**: array

**maxLength**: 32

###### items
**type**: string

####### enum
- device
- week
- time
- keyword
**name**: condition_type

**in**: query

**description**: 配信条件がキーワード場合

出力条件

and

or

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

###### enum
- and
- or
**name**: device_type

**in**: query

**description**: 配信条件設定が端末の場合

端末情報

pc：PC

ios：iOS

android：Android

**required**: False

**explode**: False

##### schema
**type**: array

**maxLength**: 32

###### items
**type**: string

####### enum
- pc
- ios
- android
**name**: condition_week

**in**: query

**description**: 配信条件設定が曜日の場合

曜日情報

0：日

1：月

2：火

3：水

4：木

5：金

6：土

**required**: False

**explode**: False

##### schema
**type**: array

**maxLength**: 32

**minItems**: 0

**maxItems**: 6

###### items
**type**: integer

**format**: int32

**name**: condition_time

**in**: query

**description**: 配信条件が時間の場合

時間情報

H00、H01、……　H23（0時から23時）

※設定された時間を全て出力


範囲指定のため、出力値は以下時刻を定義

  指定開始時間：H00（0時00分）

  指定終了時間：H23（23時59分）

**required**: False

**explode**: False

##### schema
**type**: array

**maxLength**: 32

###### items
**type**: string

**pattern**: ^[H]([01][0-9]|2[0-3])$

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
**$ref**: ../components/schemas/media_space_trigger.yaml#/search

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
- 配信条件
**summary**: 配信条件 取得（1件）

**description**: 広告枠の配信条件を1件取得します。

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

**description**: 配信条件のIDを入力してください。

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
**$ref**: ../components/schemas/media_space_trigger.yaml#/info

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

### Media Type

**ファイルパス**: `src/v1/paths/media_type.yaml`

## search
### get
#### tags
- メディアタイプ
**summary**: メディアタイプ 取得（複数）

**description**: メディア情報｜メディアタイプのマスター情報を複数件取得します。
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
**$ref**: ../components/schemas/media_type.yaml#/search

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
- メディアタイプ
**summary**: メディアタイプ 取得（1件）

**description**: メディア情報｜メディアタイプのマスター情報を1件取得します。

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

**description**: メディアタイプのIDを入力してください。

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
**$ref**: ../components/schemas/media_type.yaml#/info

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

### Movie Size

**ファイルパス**: `src/v1/paths/movie_size.yaml`

## search
### get
#### tags
- 動画サイズ
**summary**: 動画サイズ 取得（複数）

**description**: 広告素材情報｜動画素材に設定できる動画サイズを複数件取得します。
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

**name**: movie_size_x

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

**name**: movie_size_y

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
**$ref**: ../components/schemas/movie_size.yaml#/search

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
- 動画サイズ
**summary**: 動画サイズ 取得（1件）

**description**: 広告素材情報｜動画素材に設定できる動画サイズを1件取得します。

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

**description**: 動画サイズのIDを入力してください。

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
**$ref**: ../components/schemas/movie_size.yaml#/info

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
