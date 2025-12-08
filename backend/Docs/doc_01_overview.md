# アフィリコード・システム API v1 完全ドキュメント

**生成日時**: 2025-11-15 10:18:37

---

## OpenAPI仕様書

```yaml
openapi: 3.0.3
info:
  # APIのタイトル
  title: アフィリコード・システム API v1

  # APIの概要
  description: |-
    # はじめに

    ## APIドキュメントの取り扱いについて

    株式会社リーフワークス（以下、当社）が提供するアフィリエイト広告配信システム「アフィリコード・システム」における、外部システム連携用のAPI概要及び項目定義を記載した仕様書です。

    - 本ドキュメントの一部または全てを改編、引用することを禁じます。
    - 本ドキュメントのURLを第三者に共有することを禁じます。
    - 当社が所有する知的財産権に基づいた重要な技術情報を含んでいます。
    - 本ドキュメントに基づいて知的財産権の対象物を成したとき、その権利は、当社に帰属するものとします。
    - 機密情報として規定される情報の一部を構成します。取り扱いについては十分にご注意ください。

    # 共通仕様

    本API（Application Programming Interface）は、アフィリコード・システム（以下、ACS）が提供するデータを外部のアプリケーションやプログラムから扱うための機能を提供するインターフェースです。HTTP通信を利用し、RESTful APIのガイドラインに沿って設計されています。リクエストURIに要求された情報を付与し、該当データをJSON形式で返却します。

    ## APIキーの取得

    APIの利用に際し、APIキーで認証を行います。APIキーは管理者アカウントごとに発行されます。

    管理者権限でACSにログインし、管理者情報のアカウント詳細画面よりAPIキー（アクセスキー、シークレットキー）を取得します。

    リクエストヘッダに、以下のような書式で設定します。

    ※シークレットキーは、管理画面より再発行が可能です。

    `{アクセスキー}:{シークレットキー}`

    ※コロンで結合

    # クエリパラメータ

    ## 取得（集計値）

    - クエリパラメータで検索条件を指定して、成果集計情報を取得することができます。
    - クエリパラメータ、レスポンスについては、各API取得情報を参照してください。

    ### 項目形式：文字列

    検索項目が「文字列」の場合

    | 検索パターン | 検索内容                        |
    |-------------|--------------------------------|
    | 単一条件検索 | 指定フィールドに対して、単一条件で検索を行う<br><br>＜マッチタイプ＞<br>完全一致検索<br><br>＜記述形式＞<br>`{フィールド名}=指定情報のID`<br><br>＜記述例＞<br>`user=ufwsr8ytwmgd` |
    | 複数条件検索 | 指定フィールドに対して、複数条件のOR検索を行う<br>＜マッチタイプ＞<br>完全一致検索<br><br>＜記述形式＞<br>`{フィールド名}[]=指定情報のID 　（複数指定可能）`<br><br>＜記述例＞<br>`user[]=ufwsr8ytwmgd&user[]=ufwsr8ytwmga`|

    ### 項目形式：数値

    検索項目が「数値」の場合

    | 検索パターン | 検索内容 |
    | ----------- | --------|
    | 単一条件検索 | 指定フィールドに対して、単一条件で検索を行う<br><br>＜使用条件＞<br>設定値は、数値（設定値が不正の場合、当該パラメータを無効とする）<br><br>＜記述形式＞<br>`{フィールド名}=数値`<br><br>＜記述例＞<br>`date_y=2021` |
    | 複数条件検索 | 指定フィールドに対して、複数条件のOR検索を行う<br><br>＜使用条件＞<br>設定値は、数値（設定値が不正の場合、当該パラメータを無効とする）<br><br>＜記述形式＞<br>`{フィールド名}[]=数値　（複数指定可能）`<br><br>＜記述例＞<br>`date_y[]=2021&date_y[]=2022` |
    | 範囲検索     | 指定フィールドに対して、数値の範囲検索を行う<br><br>＜使用条件＞<br>設定値は、数値（設定値が不正の場合、当該パラメータを無効とする）<br>パラメータの省略は、不可<br>（パラメータの組み合わせが不正な場合、当該パラメータを無効とする）<br><br>＜記述形式＞<br>`{フィールド名}=between&{フィールド名}_A=下限値&{フィールド名}_B=上限値`<br><br>＜記述例＞<br>`date_y=between&date_y_A=2021&date_y_B=2022` |

    ### 項目形式：日付

    検索項目が「日付」の場合

    | 検索パターン | 検索内容 |
    | ----------- | --------|
    | 範囲検索     | unixtime形式のフィールドに対して、期間の範囲検索を行う<br><br>＜使用条件＞<br>設定値は、unixtime形式（設定値が不正の場合、当該パラメータを無効とする）<br>パラメータの省略は、不可<br>（パラメータの組み合わせが不正な場合、当該パラメータを無効とする）<br><br>＜記述形式＞<br>`{フィールド名}=between&{フィールド名}_A=下限値&{フィールド名}_B=上限値`<br><br>＜記述例＞<br>`date_unix=between&date_unix_A=1609426800&date_unix_B=1640962799` |
    | 日付検索     | unixtime形式のフィールドに対して、期間の範囲検索を行う<br><br>＜使用条件＞<br>設定値は、数値（設定値が不正の場合、当該パラメータを無効とする）<br>パラメータの省略は、不可<br>（パラメータの組み合わせが不正な場合、当該パラメータを無効とする）<br>下限値の時間は、0時0分0秒で、上限値の時間は、23時59分59秒として検索する<br><br>＜記述形式＞<br>`{フィールド名}=between_date&{フィールド名}_A_Y=年（4桁）&{フィールド名}_A_M=月（1，2桁）&{フィールド名}_A_D=日（1、2桁）&{フィールド名}_B_Y=年（4桁）&{フィールド名}_B_M=月（1，2桁）&{フィールド名}_B_D=日（1、2桁）`<br><br>＜記述例＞<br>`regist_unix=between_date&regist_unix_A_Y=2021&regist_unix_A_M=1&regist_unix_A_D=1&regist_unix_B_Y=2021&regist_unix_B_M=12&regist_unix_B_D=31`|


    ## 取得（1件）

    ### 共通設定

    - レコードIDを指定して、レコード情報を1件取得することができます。
    - レスポンスについては、各API取得情報を参照してください。

    | パラメータ | 設定内容 |
    | --------- | --------|
    | id        | 対象情報のレコードIDを示す。<br><br>＜使用条件＞<br>存在するレコードIDを指定<br>省略時、または、存在しないレコードIDを指定した場合、エラー[400]<br>ただし、システム情報を取得するAPIは、当該パラメータは不要 |

    ## 取得（複数）

    ### 共通設定

    - クエリパラメータで検索条件を指定して、複数のレコードを取得することができます。
    - レスポンスについては、各API取得情報を参照してください。
    - 一度に取得できるレコード数は最大500件です。（取得レコード数を任意に指定する場合、limitパラメータを使用）

    | パラメータ          | 設定内容 |
    | ------------------ | --------|
    | offset             | 取得するレコードの開始位置を示す。<br><br>＜使用条件＞<br>有効値：0以上　省略時：0 |
    | limit              | 取得するレコード数を示す。<br><br>＜使用条件＞<br>有効値：1～500（501以上を指定すると、エラー[400]）　省略時：100 |
    | order_key<br>order | 取得するレコードのソート条件を示す。<br><br>＜使用条件＞<br>利用する場合は、両パラメータを使用<br>（片方のみ、または、パラメータの設定値が不正の場合は、初期ソート）<br>省略時は、各APIの初期ソートに準拠<br><br>＜記述形式＞<br>`order_key={フィールド名}&order=ASC、または、DESC`<br>ASC：昇順　DESC：降順<br><br>＜記述例＞<br>`order_key=regist_unix&order=ASC` |
    | keyword            | フリーワード検索用のパラメータを示す。<br><br>＜使用条件＞<br>検索対象のフィールドは、各API仕様書のクエリパラメータ｜フリーワード欄を参照<br><br>＜マッチタイプ＞<br>部分一致検索<br><br>＜記述形式＞<br>keyword=文字列、または、数値<br><br>＜記述例＞<br>`keyword=株式会社リーフワークス` |

    ### 項目形式：文字列

    検索項目が「文字列」の場合

    | 検索パターン | 検索内容 |
    | ----------- | --------|
    | 単一条件検索 | 指定フィールドに対して、単一条件で検索を行う<br><br>＜マッチタイプ＞<br>部分一致検索<br><br>＜記述形式＞<br>`{フィールド名}=文字列、または、数値`<br><br>＜記述例＞<br>`company=株式会社リーフワークス` |
    | 複数条件検索 | 指定フィールドに対して、複数条件のOR検索を行う <br><br>＜マッチタイプ＞<br>完全一致検索<br><br>＜記述形式＞<br>`{フィールド名}[]=文字列、または、数値　　（複数指定可能）`<br><br>＜記述例＞<br>`state[]=1&state[]=2` |

    ### 項目形式：数値

    検索項目が「数値」の場合

    | 検索パターン | 検索内容 |
    | ----------- | --------|
    | 単一条件検索 | 指定フィールドに対して、単一条件で検索を行う<br><br>＜使用条件＞<br>設定値は、数値（設定値が不正の場合、当該パラメータを無効とする）<br><br>＜記述形式＞<br>`{フィールド名}=数値`<br><br>＜記述例＞<br>`gross_action_cost=3000` |
    | 複数条件検索 | 指定フィールドに対して、複数条件のOR検索を行う<br><br>＜使用条件＞<br>`設定値は、数値（設定値が不正の場合、当該パラメータを無効とする）`<br><br>＜記述形式＞<br>`{フィールド名}[]=数値　（複数指定可能）`<br><br>＜記述例＞<br>`gross_action_cost[]=3000&gross_action_cost[]=5000` |
    | 範囲検索     | 指定フィールドに対して、数値の範囲検索を行う<br><br>＜使用条件＞<br>設定値は、数値（設定値が不正の場合、当該パラメータを無効とする）<br>パラメータの省略は、不可（パラメータの組み合わせが不正な場合、当該パラメータを無効とする）<br><br>＜記述形式＞<br>`{フィールド名}=between&{フィールド名}_A=下限値&{フィールド名}_B=上限値`<br><br>＜記述例＞<br>`gross_action_cost=between&gross_action_cost_A=1000&gross_action_cost_B=3000` |

    ### 項目形式：配列

    検索項目が「配列」の場合

    ※指定フィールドに対して同じデータ形式の値をまとめて扱っている形の場合

    | 検索パターン      |               | 検索内容 |
    | -----------------|-------------- | --------|
    | 単一条件検索      |               | 指定フィールドに対して、単一条件で検索を行う<br><br>＜記述形式＞<br>`{フィールド名}=文字列、または、数値`<br><br>＜記述例＞<br>`promotion_type=action` |
    | 複数条件検索      | OR検索         | 指定フィールドに対して、複数条件のOR検索を行う<br><br>＜記述形式＞<br>`{フィールド名}_SP=LIKE_OR&{フィールド名}[]=文字列、または、数値`（複数指定可能）<br><br>＜記述例＞<br>`promotion_type_SP=LIKE_OR&promotion_type[]=action&promotion_type[]=click` |
    |                  | AND検索        | 指定フィールドに対して、複数条件のAND検索を行う<br><br>＜記述形式＞<br>`{フィールド名}_SP=LIKE_AND&{フィールド名}[]=文字列、または、数値`（複数指定可能）<br><br>＜記述例＞<br>`promotion_type_SP=LIKE_AND&promotion_type[]=action&promotion_type[]=click` |

    ### 項目形式：日付

    検索項目が「日付」の場合

    | 検索パターン | 検索内容 |
    | ----------- | --------|
    | 範囲検索     | unixtime形式のフィールドに対して、期間の範囲検索を行う<br><br>＜使用条件＞<br>設定値は、unixtime形式（設定値が不正の場合、当該パラメータを無効とする）<br>パラメータの省略は、不可（パラメータの組み合わせが不正な場合、当該パラメータを無効とする）<br><br>＜記述形式＞<br>`{フィールド名}=between&{フィールド名}_A=下限値&{フィールド名}_B=上限値`<br><br>＜記述例＞<br>`regist_unix=between&regist_unix_A=1609426800&regist_unix_B=1640962799` |
    | 日付検索     | unixtime形式のフィールドに対して、期間の範囲検索を行う<br><br>＜使用条件＞<br>設定値は、数値（設定値が不正の場合、当該パラメータを無効とする）<br>パラメータの省略は、不可（パラメータの組み合わせが不正な場合、当該パラメータを無効とする）<br>下限値の時間は、0時0分0秒で、上限値の時間は、23時59分59秒として検索する<br><br>＜記述形式＞<br>`{フィールド名}=between_date&{フィールド名}_A_Y=年（4桁）&{フィールド名}_A_M=月（1，2桁）&{フィールド名}_A_D=日（1、2桁）&{フィールド名}_B_Y=年（4桁）&{フィールド名}_B_M=月（1，2桁）&{フィールド名}_B_D=日（1、2桁）`<br><br>＜記述例＞<br>`regist_unix=between_date&regist_unix_A_Y=2021&regist_unix_A_M=1&regist_unix_A_D=1&regist_unix_B_Y=2021&regist_unix_B_M=12&regist_unix_B_D=31`|

  # APIドキュメントのバージョン
  version: 1.7.1
  x-logo:
    url: '../src/common/images/logo_acs-hor.svg'
    altText: Affilicode System Logo
    href: '#'

servers:
  # 外部ドキュメントのURL
  - url: https://<ドメイン名>/api/v1/m

paths:
  # 各エンドポイントのパス
  /access_log/search:
    $ref: ../src/v1/paths/access_log.yaml#/search
  /access_log/sum:
    $ref: ../src/v1/paths/access_log.yaml#/sum
  /click_log/search:
    $ref: ../src/v1/paths/click_log.yaml#/search
  /click_log/sum:
    $ref: ../src/v1/paths/click_log.yaml#/sum
  /imp_log/search:
    $ref: ../src/v1/paths/imp_log.yaml#/search
  /imp_log/sum:
    $ref: ../src/v1/paths/imp_log.yaml#/sum
  /action_log_raw/search:
    $ref: ../src/v1/paths/action_log_raw.yaml#/search
  /action_log_raw/info:
    $ref: ../src/v1/paths/action_log_raw.yaml#/info
  /action_log/sum:
    $ref: ../src/v1/paths/action_log.yaml#/sum
  /check_log_raw/search:
    $ref: ../src/v1/paths/check_log_raw.yaml#/search
  /check_log_raw/info:
    $ref: ../src/v1/paths/check_log_raw.yaml#/info
  /track_log/search:
    $ref: ../src/v1/paths/track_log.yaml#/search
  /track_log/info:
    $ref: ../src/v1/paths/track_log.yaml#/info
  /user/regist:
    $ref: ../src/v1/paths/user.yaml#/regist
  /user/search:
    $ref: ../src/v1/paths/user.yaml#/search
  /user/info:
    $ref: ../src/v1/paths/user.yaml#/info
  /user/edit:
    $ref: ../src/v1/paths/user.yaml#/edit
  /user_group/search:
    $ref: ../src/v1/paths/user_group.yaml#/search
  /user_group/info:
    $ref: ../src/v1/paths/user_group.yaml#/info
  /media/regist:
    $ref: ../src/v1/paths/media.yaml#/regist
  /media/search:
    $ref: ../src/v1/paths/media.yaml#/search
  /media/info:
    $ref: ../src/v1/paths/media.yaml#/info
  /media/edit:
    $ref: ../src/v1/paths/media.yaml#/edit
  /media_space/regist:
    $ref: ../src/v1/paths/media_space.yaml#/regist
  /media_space/search:
    $ref: ../src/v1/paths/media_space.yaml#/search
  /media_space/info:
    $ref: ../src/v1/paths/media_space.yaml#/info
  /media_space_trigger/search:
    $ref: ../src/v1/paths/media_space_trigger.yaml#/search
  /media_space_trigger/info:
    $ref: ../src/v1/paths/media_space_trigger.yaml#/info
  /media_space_item/regist:
    $ref: ../src/v1/paths/media_space_item.yaml#/regist
  /media_space_item/search:
    $ref: ../src/v1/paths/media_space_item.yaml#/search
  /media_space_item/info:
    $ref: ../src/v1/paths/media_space_item.yaml#/info
  /ssp_space/search:
    $ref: ../src/v1/paths/ssp_space.yaml#/search
  /ssp_space/info:
    $ref: ../src/v1/paths/ssp_space.yaml#/info
  /media_category/search:
    $ref: ../src/v1/paths/media_category.yaml#/search
  /media_category/info:
    $ref: ../src/v1/paths/media_category.yaml#/info
  /media_type/search:
    $ref: ../src/v1/paths/media_type.yaml#/search
  /media_type/info:
    $ref: ../src/v1/paths/media_type.yaml#/info
  /advertiser/search:
    $ref: ../src/v1/paths/advertiser.yaml#/search
  /advertiser/info:
    $ref: ../src/v1/paths/advertiser.yaml#/info
  /promotion/regist:
    $ref: ../src/v1/paths/promotion.yaml#/regist
  /promotion/search:
    $ref: ../src/v1/paths/promotion.yaml#/search
  /promotion/info:
    $ref: ../src/v1/paths/promotion.yaml#/info
  /promotion/edit:
    $ref: ../src/v1/paths/promotion.yaml#/edit
  /promotion_category/search:
    $ref: ../src/v1/paths/promotion_category.yaml#/search
  /promotion_category/info:
    $ref: ../src/v1/paths/promotion_category.yaml#/info
  /promotion_device/search:
    $ref: ../src/v1/paths/promotion_device.yaml#/search
  /promotion_device/info:
    $ref: ../src/v1/paths/promotion_device.yaml#/info
  /promotion_icon/search:
    $ref: ../src/v1/paths/promotion_icon.yaml#/search
  /promotion_icon/info:
    $ref: ../src/v1/paths/promotion_icon.yaml#/info
  /promotion_item/regist:
    $ref: ../src/v1/paths/promotion_item.yaml#/regist
  /promotion_item/search:
    $ref: ../src/v1/paths/promotion_item.yaml#/search
  /promotion_item/info:
    $ref: ../src/v1/paths/promotion_item.yaml#/info
  /promotion_item/edit:
    $ref: ../src/v1/paths/promotion_item.yaml#/edit
  /promotion_apply/regist:
    $ref: ../src/v1/paths/promotion_apply.yaml#/regist
  /promotion_apply/search:
    $ref: ../src/v1/paths/promotion_apply.yaml#/search
  /promotion_apply/info:
    $ref: ../src/v1/paths/promotion_apply.yaml#/info
  /promotion_apply/edit:
    $ref: ../src/v1/paths/promotion_apply.yaml#/edit
  /promotion_deny/search:
    $ref: ../src/v1/paths/promotion_deny.yaml#/search
  /promotion_deny/info:
    $ref: ../src/v1/paths/promotion_deny.yaml#/info
  /promotion_given/regist:
    $ref: ../src/v1/paths/promotion_given.yaml#/regist
  /promotion_given/search:
    $ref: ../src/v1/paths/promotion_given.yaml#/search
  /promotion_given/info:
    $ref: ../src/v1/paths/promotion_given.yaml#/info
  /promotion_given/edit:
    $ref: ../src/v1/paths/promotion_given.yaml#/edit
  /promotion_cost/regist:
    $ref: ../src/v1/paths/promotion_cost.yaml#/regist
  /promotion_cost/search:
    $ref: ../src/v1/paths/promotion_cost.yaml#/search
  /promotion_cost/info:
    $ref: ../src/v1/paths/promotion_cost.yaml#/info
  /promotion_cost/edit:
    $ref: ../src/v1/paths/promotion_cost.yaml#/edit
  /promotion_table/search:
    $ref: ../src/v1/paths/promotion_table.yaml#/search
  /promotion_table/info:
    $ref: ../src/v1/paths/promotion_table.yaml#/info
  /promotion_goods/search:
    $ref: ../src/v1/paths/promotion_goods.yaml#/search
  /promotion_goods/info:
    $ref: ../src/v1/paths/promotion_goods.yaml#/info
  /promotion_goods_cost/search:
    $ref: ../src/v1/paths/promotion_goods_cost.yaml#/search
  /promotion_goods_cost/info:
    $ref: ../src/v1/paths/promotion_goods_cost.yaml#/info
  /promotion_change/search:
    $ref: ../src/v1/paths/promotion_change.yaml#/search
  /promotion_change/info:
    $ref: ../src/v1/paths/promotion_change.yaml#/info
  /banner_size/search:
    $ref: ../src/v1/paths/banner_size.yaml#/search
  /banner_size/info:
    $ref: ../src/v1/paths/banner_size.yaml#/info
  /movie_size/search:
    $ref: ../src/v1/paths/movie_size.yaml#/search
  /movie_size/info:
    $ref: ../src/v1/paths/movie_size.yaml#/info
  /media_facebook/search:
    $ref: ../src/v1/paths/media_facebook.yaml#/search
  /media_facebook/info:
    $ref: ../src/v1/paths/media_facebook.yaml#/info
  /system/info:
    $ref: ../src/v1/paths/system.yaml#/info
```

---

## フラウド検知向けログ取得メモ

- IP/UA を使う場合は `/track_log/search` が本命。レスポンスに `ipaddress` / `useragent` / `referrer` などが含まれる。パラメータは `limit` (最大500) と `offset`（0始まり）を使用し、日付絞り込みは `regist_unix=between_date` と `regist_unix_A_Y/M/D`、`regist_unix_B_Y/M/D` を指定する。
- `/access_log/search` は ID と日付メタ中心で IP/UA は含まれないため、IP/UA重複検知には不向き。`/click_log/search` は CPC課金ログのみ。
- ブラウザ由来に絞る場合は、取得後に UA ブラックリスト（bot/crawler 等）・プライベートIP除外を適用し、フィルタ済みデータで集計する。
