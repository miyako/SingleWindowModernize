# 用語集 / Glossary

Keep terminology consistent across `src/<target>.md` and `figures/*.<target>.txt`.
Change an entry here first, then search and replace in both places.

Style (ja): です・ます調. Half-width alphanumerics, no space between Japanese and Latin text (e.g. `4D.Vector型`).
Full-width `（）` and `：` in prose. Do not routinely append English glosses to Japanese terms, even on first occurrence.
Keep English equivalents in this glossary; preserve identifiers, UI labels, URLs and necessary original abbreviations in the text.

## 4D terms (from the official 4D Japanese documentation)

| English | 日本語 | Notes |
|---|---|---|
| entity / entity selection | エンティティ / エンティティセレクション | |
| datastore | データストア | |
| dataclass | データクラス | |
| attribute | 属性 | |
| computed attribute | 計算属性 | |
| collection | コレクション | |
| object | オブジェクト | |
| method | メソッド | |
| project method | プロジェクトメソッド | |
| function | 関数 | |
| class | クラス | |
| parameter | 引数 | |
| form | フォーム | |
| form object | フォームオブジェクト | |
| list box | リストボックス | |
| web area | Webエリア | |
| 4D Web Server | 4D Webサーバー | |
| worker | ワーカー | |
| process | プロセス | |
| query | クエリ | |
| formula | フォーミュラ | |
| component | コンポーネント | |

## Document-specific terms

| English | 日本語 | Notes |
|---|---|---|
| technical note | テクニカルノート | |
| end user | エンドユーザー | |
| modernize / modernization | モダナイズする / モダナイズ | 初稿の表記。編集時の確認対象。 |
| single window / Single Window app | シングルウィンドウ / シングルウィンドウアプリ | 単一のウィンドウで一覧と詳細を扱う構成。表紙タイトルは編集者指定の「シングルウィンドウアプリケーション」。 |
| toolbar | ツールバー | |
| ribbon bar | リボンバー | |
| user-customizable | ユーザーがカスタマイズ可能な | |
| preview area / preview mode | プレビューエリア / プレビューモード | |
| output form / input form | 出力フォーム / 入力フォーム | |
| subform | サブフォーム | |
| project form / form method / object method | プロジェクトフォーム / フォームメソッド / オブジェクトメソッド | |
| project mode | プロジェクトモード | |
| Classic Language | クラシック言語 | |
| data source | データソース | |
| expression / expression type | 式 / 式の型 | プロパティリスト内の正式な日本語UI表記はスクリーンショットの確認時に照合。 |
| callback method | コールバックメソッド | |
| event / form event | イベント / フォームイベント | `On Load`などの識別子は変更しない。 |
| constructor | コンストラクター | |
| property | プロパティ | |
| priority | 優先度 | |
| tooltip | ツールチップ | |
| alternate action | 代替アクション | 右側の矢印でコンテキストメニューを開くボタンの動作。初稿の表記。 |
| context menu | コンテキストメニュー | |
| search box / search picker | 検索ボックス / 検索ピッカー | ウィジェット名`SearchPicker`は変更しない。 |
| splitter | スプリッター | |
| alias | エイリアス | |
| optimistic locking | 楽観的ロック | |
| auto merge | 自動マージ | 定数`dk auto merge`などは変更しない。 |
| record | レコード | ORDAのエンティティとは文脈に応じて区別。 |
| custom field | カスタムフィールド | |
| Single User mode | シングルユーザーモード | |
| client/server mode | クライアント/サーバーモード | |
| SDI / Single Document Interface | SDI / Single Document Interface | 略語と展開形は原文どおり。 |
| network traffic | ネットワークトラフィック | |
| server load | サーバー負荷 | |
| packet / packet exchange | パケット / パケットのやり取り | |
| latency | レイテンシー | |
| bandwidth | 帯域幅 | |
| local cache | ローカルキャッシュ | |
| class function | クラス関数 | |
| form context | フォームコンテキスト | |
| table / field / header | テーブル / フィールド / ヘッダー | |
| data file / log file | データファイル / ログファイル | |
| out / in | out / in | 原文のログ測定値のラベルを維持。単位はkbyteのままとし、KiBへの換算は行わない。 |
| framework | フレームワーク | |

## Proper nouns in examples

| English | 日本語 | Notes |
|---|---|---|
| Single Window App – Modernize your application | シングルウィンドウアプリケーション | 編集者指定の表紙タイトル。著者表記は「Thomas Maul（4D Germany）」。テクニカルノート番号は日本語PDFの表紙には表示しない。 |
| Thomas Maul | Thomas Maul | 著者名を維持。 |
| 4D Germany | 4D Germany | 著者の所属表記を維持。 |
| 4D Invoice / 4D Invoices | 4D Invoice / 4D Invoices | 同じサンプルの名称が原文中で揺れているため、各出現箇所の表記を維持。 |
| Microsoft Outlook | Microsoft Outlook | |
| Windows / Mac | Windows / Mac | 原文のプラットフォーム名を維持。 |
| Ethernet | Ethernet | |
| ORDA | ORDA | |
| 4D Tour | 4D Tour | |
| 4D Server | 4D Server | |
| SearchPicker | SearchPicker | ウィジェット名・サブフォーム名。翻訳しない。 |
| Toolbar / Toolbar_Button / Toolbar_Setup / ORDA_Listbox | 原文どおり | クラス名・フォーム名・識別子。翻訳しない。 |
| ORDAListbox / CLIENTS / Projects / Input / Input_ORDA | 原文どおり | フォーム名・テーブル名などの識別子。翻訳しない。 |
| ORDA_Listbox_Method / ORDA_Listbox_method / ODA_Listbox_method | 原文どおり | 大文字小文字や`ODA`の表記も原文どおり。黙ってコードや参照先を修正しない。 |
| Settings / Toolbar Setup / Reset | Settings / Toolbar Setup / Reset | 英語スクリーンショットに対応する操作ラベルとして維持。日本語UIラベルの承認後に再確認。 |
| All / Selected / None / Query / Sort / Print | 原文どおり | 本文中のボタン名は、英語UI・識別子との対応を優先して維持。 |

## Demo UI draft

The following entries apply to the Japanese demo UI. The manuscript's English screenshot labels remain unchanged
until the screenshot review; database, form, method, field and action identifiers are never renamed.

| English | 日本語 | Notes |
|---|---|---|
| Customers / Clients | 顧客 | デモの表示名。`CLIENTS`などの識別子は維持。 |
| Invoices | 請求書 | |
| Products | 商品 | |
| Settings | 設定 | デモの表示名のみ。本文中の英語操作ラベルは未変更。 |
| Name | 名称 | 汎用の属性見出し。 |
| Address / City / State / Postcode | 住所 / 市区町村 / 都道府県 / 郵便番号 | |
| Contact / Comments | 担当者 / 備考 | |
| Subtotal / Tax / Total | 小計 / 税額 / 合計 | |
| Unit price / Tax rate / Discount rate | 単価 / 税率 / 割引率 | 元の税率や金額を日本向けに換算しない。 |
| Pro forma | 仮請求書 | デモUIの初稿。 |
| Payment method / Payment reference | 支払方法 / 支払参照 | 生成する参照値はデモ用と明示。 |
| By check / By credit card / By bank transfer | 小切手 / クレジットカード / 銀行振込 | |
| Multifunction pen / Fountain pen / Ballpoint pen / Rollerball pen | 多機能ペン / 万年筆 / ボールペン / ローラーボールペン | 表示名のみ。商品コードの元文字列は維持。 |
| Black / Red / Blue / Yellow / Green / White | 黒 / 赤 / 青 / 黄 / 緑 / 白 | |
| Bright red / Bright blue / Bright yellow / Bright green | 明るい赤 / 明るい青 / 明るい黄 / 明るい緑 | |
| Invoice demo (fictional data) | 請求書デモ（架空データ） | 合成データであることをウィンドウタイトルにも明示。 |
| Invoice lines / Quantity / Product reference | 請求明細 / 数量 / 商品コード | 元の式・商品コードは変更しない。 |
| Discount value / VAT rate | 割引額 / 税率 | 既存の税率を日本の税率として扱わない。 |
| Total with tax / Total excluding tax | 税込合計 / 税抜合計 | 帳票の表示ラベルのみ。 |
| Document template / Field list | 文書テンプレート / フィールド一覧 | |
