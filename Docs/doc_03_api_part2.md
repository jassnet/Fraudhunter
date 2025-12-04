## APIエンドポイント詳細

### get
#### tags
- バナーサイズ
**summary**: バナーサイズ 取得（複数）

**description**: 広告素材情報｜テンプレート素材に設定できるバナーサイズを複数件取得します。
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

**name**: banner_size_x

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

**name**: banner_size_y

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
**$ref**: ../components/schemas/banner_size.yaml#/search

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
- バナーサイズ
**summary**: バナーサイズ 取得（1件）

**description**: 広告素材情報｜テンプレート素材に設定できるバナーサイズのマスター情報を1件取得します。

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

**description**: バナーサイズのIDを入力してください。

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
**$ref**: ../components/schemas/banner_size.yaml#/info

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

### Check Log Raw

**ファイルパス**: `src/v1/paths/check_log_raw.yaml`

## search
### get
#### tags
- チェックログ
**summary**: チェックログ取得（複数）

**description**: チェックログ情報を複数件取得します。

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

**name**: plid

**in**: query

**description**: plid

**required**: False

**explode**: False

##### schema
**type**: string

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

**name**: args

**in**: query

**description**: args（成果識別子）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

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

**name**: state

**in**: query

**description**: ステータス

0：無効

1：有効（成果発生なし）

2：有効（成果発生あり）

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 1
- 2
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
**$ref**: ../components/schemas/check_log_raw.yaml#/search

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
- チェックログ
**summary**: チェックログ取得（1件）

**description**: チェックログ情報を１件取得します。

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

**description**: チェックログのIDを入力してください。

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
**$ref**: ../components/schemas/check_log_raw.yaml#/info

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

### Click Log

**ファイルパス**: `src/v1/paths/click_log.yaml`

## search
### get
#### tags
- クリック報酬
**summary**: クリック報酬 取得（複数）

**description**: クリック報酬を複数件取得します。初期ソートは、登録日時の降順です。

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
########## header
**$ref**: ../components/schemas/header.yaml

########## records
**$ref**: ../components/schemas/click_log.yaml#/search

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
- クリック報酬
**summary**: クリック報酬 取得（集計値）

**description**: クリック報酬の集計値を取得します。

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
############ click
**type**: integer

**format**: int32

**description**: クリック数

クリック数の集計値

############ net_reward
**type**: integer

**format**: int32

**description**: クリック報酬額（ネット）

クリック報酬額（ネット）の集計値

############ gross_reward
**type**: integer

**format**: int32

**description**: クリック報酬額（グロス）

クリック報酬額（グロス）の集計値

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

### Imp Log

**ファイルパス**: `src/v1/paths/imp_log.yaml`

## search
### get
#### tags
- インプレッションログ
**summary**: インプレッションログ 取得（複数）

**description**: インプレッションログを複数件取得します。初期ソートは、登録日時の降順です。

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
########## header
**$ref**: ../components/schemas/header.yaml

########## records
**$ref**: ../components/schemas/imp_log.yaml#/search

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
- インプレッションログ
**summary**: インプレッションログ 取得（集計値）

**description**: インプレッションログの集計値を取得します。

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
############ imp
**type**: integer

**format**: int32

**description**: インプレッション数

インプレッション数の集計値

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

### Media

**ファイルパス**: `src/v1/paths/media.yaml`

## search
### get
#### tags
- メディア
**summary**: メディア 取得（複数）

**description**: メディア情報を複数件取得します。
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

**name**: name

**in**: query

**description**: メディア名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: url

**in**: query

**description**: メディアURL

**required**: False

**explode**: False

##### schema
**type**: string

**name**: media_category

**in**: query

**description**: メディアカテゴリー

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: media_type

**in**: query

**description**: メディアタイプ

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: pv_row

**in**: query

**description**: 月間PV数

0：未設定

100：100以下

500：500以下

1000：1000以下

3000：3000以下

10000：1万以下

50000：5万以下

100000：10万未満

100001：10万以上

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 100
- 500
- 1000
- 3000
- 10000
- 50000
- 100000
- 100001
**name**: uu_row

**in**: query

**description**: 月間UU数

0：未設定

10：10以下

50：50以下

100：100以下

500：500以下

1000：1000未満

1001：1000以上

**required**: False

**explode**: False

##### schema
**type**: integer

**format**: int32

###### enum
- 0
- 10
- 50
- 100
- 500
- 1000
- 1001
**name**: comment

**in**: query

**description**: メディア説明

**required**: False

**explode**: False

##### schema
**type**: string

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

**name**: link_pbid

**in**: query

**description**: 広告URLパラメータ変換（pbid）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: link_kbp1

**in**: query

**description**: 広告URLパラメータ変換（kbp1）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: link_kbp2

**in**: query

**description**: 広告URLパラメータ変換（kbp2）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: link_kbp3

**in**: query

**description**: 広告URLパラメータ変換（kbp3）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: link_pcp

**in**: query

**description**: 広告URLパラメータ変換（pcp）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: link_args

**in**: query

**description**: 広告URLパラメータ変換（args）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: link_pm1

**in**: query

**description**: 広告URLパラメータ変換（pm1）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: link_pm2

**in**: query

**description**: 広告URLパラメータ変換（pm2）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: link_pm3

**in**: query

**description**: 広告URLパラメータ変換（pm3）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: link_pm4

**in**: query

**description**: 広告URLパラメータ変換（pm4）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: link_pm5

**in**: query

**description**: 広告URLパラメータ変換（pm5）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: link_plid

**in**: query

**description**: 広告URLパラメータ変換（plid）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: pb_state

**in**: query

**description**: キックバック通知設定

0：通知しない

1：全て通知（未承認・承認・キャンセル）

2：承認のみ通知（承認）

3：初回発生時のみ通知（未承認・承認）

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
- 2
- 3
**name**: pb_type

**in**: query

**description**: 成果の承認状態による通知先設定

0：利用しない

1：利用する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: pb_regist_url

**in**: query

**description**: キックバック通知先URL（未承認）

**required**: False

**explode**: False

##### schema
**type**: string

**name**: pb_apply_url

**in**: query

**description**: キックバック通知先URL（承認）

**required**: False

**explode**: False

##### schema
**type**: string

**name**: pb_cancel_url

**in**: query

**description**: キックバック通知先URL（キャンセル）

**required**: False

**explode**: False

##### schema
**type**: string

**name**: pb_pg_key

**in**: query

**description**: 商品テーブルの変数設定（変数）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: pb_pg_val

**in**: query

**description**: 商品テーブルの変数設定（設定値）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: pb_retry_state

**in**: query

**description**: リトライ設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: pb_retry_response_state

**in**: query

**description**: 
返却値チェック

0：設定しない

1：設定する


**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: pb_retry_response_text

**in**: query

**description**: 返却値

**required**: False

**explode**: False

##### schema
**type**: array

**name**: pb_retry_count

**in**: query

**description**: 最大リトライ回数

1～9

単位：回

**required**: False

**explode**: False

##### schema
**type**: integer

**minimum**: 1

**maximum**: 9

**name**: pb_retry_wait

**in**: query

**description**: リトライ間隔

1~9999

単位：分

**required**: False

**explode**: False

##### schema
**type**: integer

**minimum**: 1

**maximum**: 9999

**name**: google_cv_state

**in**: query

**description**: Google広告CV連携設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: google_cv_name

**in**: query

**description**: コンバージョンアクション名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: google_cv_report

**in**: query

**description**: 出力データの対象条件

0：発生成果（全て）

1：確定成果（承認のみ）

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: google_cv_time_type

**in**: query

**description**: 出力データの対象期間

now：実行日時

yesterday：当日0時

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 16

###### enum
- now
- yesterday
**name**: google_cv_time_val

**in**: query

**description**: 出力データの対象期間

21600：6時間

43200：12時間

86400：1日

172800：2日

604800：7日

691200：8日

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 21600
- 43200
- 86400
- 172800
- 604800
- 691200
**name**: google_cv_auth_key

**in**: query

**description**: Basic認証｜ユーザー名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: google_cv_auth_pass

**in**: query

**description**: Basic認証｜パスワード

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: fb_cv_state

**in**: query

**description**: Facebook広告CV連携設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: fb_cv_type

**in**: query

**description**: ピクセル管理者

user：アフィリエイター

advertiser：広告主

admin：管理者

**required**: False

**explode**: True

##### schema
**type**: array

###### enum
- user
- advertiser
- admin
###### example
- user
- admin
**name**: media_facebook

**in**: query

**description**: Facebook広告ピクセル

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

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

**name**: fb_cv_user_id

**in**: query

**description**: ビジネスマネージャーID（アフィリエイター）

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: fb_cv_report

**in**: query

**description**: 通知データの対象条件

0：発生成果（全て）

1：確定成果（承認のみ）

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: fb_cv_retry_state

**in**: query

**description**: リトライ設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: fb_cv_retry_count

**in**: query

**description**: 最大リトライ回数

1～9

単位：回

**required**: False

**explode**: False

##### schema
**type**: integer

**minimum**: 1

**maximum**: 9

**name**: fb_cv_retry_wait

**in**: query

**description**: リトライ間隔

1~9999

単位：分

**required**: False

**explode**: False

##### schema
**type**: integer

**minimum**: 1

**maximum**: 9999

**name**: yahoo_cv_state

**in**: query

**description**: Yahoo!広告CV連携設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: yahoo_cv_client

**in**: query

**description**: クライアントID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: yahoo_cv_secret

**in**: query

**description**: クライアントシークレット

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: yahoo_cv_account

**in**: query

**description**: アカウントID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: yahoo_cv_refresh

**in**: query

**description**: リフレッシュトークン

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: yahoo_cv_name

**in**: query

**description**: コンバージョン名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: yahoo_cv_report

**in**: query

**description**: 出力データの対象条件

0：発生成果（全て）

1：確定成果（承認のみ）

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: tiktok_cv_state

**in**: query

**description**: TikTok広告CV連携設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: tiktok_cv_pixel

**in**: query

**description**: ピクセルID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: tiktok_cv_token

**in**: query

**description**: アクセストークン

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: tiktok_cv_url

**in**: query

**description**: イベントURL

**required**: False

**explode**: False

##### schema
**type**: string

**name**: tiktok_cv_report

**in**: query

**description**: 出力データの対象条件

0：発生成果（全て）

1：確定成果（承認のみ）

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: tiktok_cv_retry_state

**in**: query

**description**: リトライ設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: tiktok_cv_retry_count

**in**: query

**description**: 最大リトライ回数

1～9

単位：回

**required**: False

**explode**: False

##### schema
**type**: integer

**minimum**: 1

**maximum**: 9

**name**: tiktok_cv_retry_wait

**in**: query

**description**: リトライ間隔

1~9999

単位：分

**required**: False

**explode**: False

##### schema
**type**: integer

**minimum**: 1

**maximum**: 9999

**name**: line_cv_state

**in**: query

**description**: LINE広告CV連携設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: line_cv_tag_id

**in**: query

**description**: LINE Tag ID

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: line_cv_token

**in**: query

**description**: アクセストークン

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: line_cv_event_name

**in**: query

**description**: イベント名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: line_cv_report

**in**: query

**description**: 出力データの対象条件

0：発生成果（全て）

1：確定成果（承認のみ）

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: line_cv_retry_state

**in**: query

**description**: リトライ設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: line_cv_retry_count

**in**: query

**description**: 最大リトライ回数

1～9

単位：回

**required**: False

**explode**: False

##### schema
**type**: integer

**minimum**: 1

**maximum**: 9

**name**: line_cv_retry_wait

**in**: query

**description**: リトライ間隔

1~9999

単位：分"

**required**: False

**explode**: False

##### schema
**type**: integer

**minimum**: 1

**maximum**: 9999

**name**: microsoft_cv_state

**in**: query

**description**: Microsoft広告CV連携設定

0：設定しない

1：設定する

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: microsoft_cv_name

**in**: query

**description**: コンバージョン名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 255

**name**: microsoft_cv_report

**in**: query

**description**: 出力データの対象条件

0：発生成果（全て）

1：確定成果（承認のみ）

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
**name**: microsoft_cv_time_type

**in**: query

**description**: 出力データの対象期間

now：実行日時

yesterday：当日0時

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 16

###### enum
- now
- yesterday
**name**: microsoft_cv_time_val

**in**: query

**description**: 出力データの対象期間

21600：6時間

43200：12時間

86400：1日

172800：2日

604800：7日

691200：8日

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 21600
- 43200
- 86400
- 172800
- 604800
- 691200
**name**: microsoft_cv_auth_key

**in**: query

**description**: Basic認証｜ユーザー名

**required**: False

**explode**: False

##### schema
**type**: string

**maxLength**: 32

**name**: microsoft_cv_auth_pass

**in**: query

**description**: Basic認証｜パスワード

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

2：保留

3：却下

**required**: False

**explode**: False

##### schema
**type**: integer

###### enum
- 0
- 1
- 2
- 3
**name**: memo

**in**: query

**description**: 管理者用メモ

**required**: False

**explode**: False

##### schema
**type**: string

**name**: edit_unix

**in**: query

**description**: 最終編集日時

**required**: False

**explode**: False

##### schema
**type**: integer

**name**: regist_unix

**in**: query

**description**: 登録日時

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
**$ref**: ../components/schemas/media.yaml#/search

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
