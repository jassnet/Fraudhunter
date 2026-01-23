## APIエンドポイント詳細

### Promotion Change

**ファイルパス**: `src/v1/paths/promotion_change.yaml`

## search
### get
#### tags
- 単価変更予約
**summary**: 単価変更予約 取得（複数）

**description**: 広告詳細｜単価変更予約情報を複数件取得します。
初期ソートは、適用日時の降順です。

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

**description**: 単価変更予約名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: net_click_cost

**in**: query

**description**: クリック単価（ネット）

0～99999999

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 0

**maximum**: 99999999

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
**name**: gross_click_cost

**in**: query

**description**: クリック単価（グロス）

0～99999999

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 0

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
**name**: change_date_unix

**in**: query

**description**: 適用日時

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
**$ref**: ../components/schemas/promotion_change.yaml#/search

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
- 単価変更予約
**summary**: 単価変更予約 取得（1件）

**description**: 広告詳細｜単価変更予約の情報を1件取得します。

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

**description**: 単価変更予約のIDを入力してください。

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
**$ref**: ../components/schemas/promotion_change.yaml#/info

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

### Promotion Cost

**ファイルパス**: `src/v1/paths/promotion_cost.yaml`

## search
### get
#### tags
- 特別単価
**summary**: 特別単価  取得（複数）

**description**: 広告詳細｜特別単価情報を複数件取得します。
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

広告情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: user_group

**in**: query

**description**: グループ

グループ情報のID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: link_pcp

**in**: query

**description**: パラメータ値

任意で設定したパラメータ

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: cost_type

**in**: query

**description**: 設定対象

user_group：グループ

user：アフィリエイター

media：メディア

link_pcp：パラメータ値

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

###### enum
- user_group
- user
- media
- link_pcp
**name**: name

**in**: query

**description**: 特別単価名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: limit_state

**in**: query

**description**: 期間設定

0：指定なし

1：範囲指定

2：開始日時指定

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
- 2
**name**: begin_date_unix

**in**: query

**description**: 開始日時

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: end_date_unix

**in**: query

**description**: 終了日時

unixtime形式

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: net_click_cost

**in**: query

**description**: 
クリック単価（ネット）

0～99999999

単位：円


**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 0

**maximum**: 99999999

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
**name**: gross_click_cost

**in**: query

**description**: クリック単価（グロス）

0～99999999

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**minimum**: 0

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
**name**: action_time_state

**in**: query

**description**: 成果発生までの期間設定

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
**name**: action_time

**in**: query

**description**: 広告クリックから成果発生までの有効期間

0～2147483647

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

**name**: action_time_type

**in**: query

**description**: 広告クリックから成果発生までの有効期間（単位）

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
**$ref**: ../components/schemas/promotion_cost.yaml#/search

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
- 特別単価
**summary**: 特別単価 取得（1件）

**description**: 広告詳細｜特別単価の情報を1件取得します。

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

**description**: 特別単価のIDを入力してください。

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
**$ref**: ../components/schemas/promotion_cost.yaml#/info

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
- 特別単価
**summary**: 特別単価登録

**description**: 特別単価の登録を行います。

#### parameters
**name**: X-Auth-Token

**in**: header

**description**: 管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

**required**: True

##### schema
**type**: string

**example**: {accessKey}:{secretKey}

#### requestBody
**$ref**: ../components/request_bodies/promotion_cost.yaml#/regist

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/promotion_cost.yaml#/info

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
- 特別単価
**summary**: 特別単価編集

**description**: 特別単価の編集を行います。

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

**description**: 情報を編集したい特別単価のIDを入力してください。

**required**: True

**explode**: False

##### schema
**type**: string

**format**: uuid

#### requestBody
**$ref**: ../components/request_bodies/promotion_cost.yaml#/edit

#### responses
##### 200
**description**: 成功

###### content
####### application/json
######## schema
**type**: object

######### properties
########## record
**$ref**: ../components/schemas/promotion_cost.yaml#/info

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

### Promotion Deny

**ファイルパス**: `src/v1/paths/promotion_deny.yaml`

## search
### get
#### tags
- 利用拒否
**summary**: 利用拒否  取得（複数）

**description**: 広告詳細｜利用拒否情報を複数件取得します。
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

**name**: user_group

**in**: query

**description**: グループ

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: deny_type

**in**: query

**description**: 設定対象

user_group：グループ

user：アフィリエイター

media：メディア

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

###### enum
- user_group
- user
- media
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
**$ref**: ../components/schemas/promotion_deny.yaml#/search

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
- 利用拒否
**summary**: 利用拒否 取得（1件）

**description**: 広告詳細｜利用拒否の情報を1件取得します。

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

**description**: 利用拒否のIDを入力してください。

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
**$ref**: ../components/schemas/promotion_deny.yaml#/info

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

### Promotion Device

**ファイルパス**: `src/v1/paths/promotion_device.yaml`

## search
### get
#### tags
- 広告デバイス
**summary**: 広告デバイス 取得（複数）

**description**: 広告情報｜広告デバイスのマスター情報を複数件取得します。
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
**$ref**: ../components/schemas/promotion_device.yaml#/search

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
