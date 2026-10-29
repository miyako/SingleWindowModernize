# シングルウィンドウアプリケーション

Single Window App – Modernize your application：日本語版。

Thomas Maul（4D Germany）によるテクニカルノート24-14の日本語版と、付属の4D Invoiceデモです。
既存の4Dアプリケーションを、一覧と詳細を同じウィンドウで扱える構成へモダナイズする方法を紹介します。
ユーザーがカスタマイズできるツールバー、列の表示や幅を変更できるリストボックス、選択したレコードのプレビューを取り上げます。

## ダウンロード

| 内容 | ファイル |
|---|---|
| 日本語PDF | [24-14_SingleWindowModernize_ja.pdf](https://github.com/miyako/SingleWindowModernize/releases/latest/download/24-14_SingleWindowModernize_ja.pdf) |
| 4Dデモ（ソースのみ） | [4D Invoice.zip](https://github.com/miyako/SingleWindowModernize/releases/latest/download/4D%20Invoice.zip) |
| 英語原文 | [24-14_SingleWindowModernize.pdf](document/24-14_SingleWindowModernize.pdf) |

## デモ

- 最低要件は4D 20 R5のプロジェクトモードです。日本語のネイティブ画面の取得にはmacOS上の4D 21 R4を使用しました。
- 展開後、`4D Invoice/Project/4D Invoice.4DProject`を開き、新しいデータファイルを作成してください。ZIPにはデータファイル、実行環境、キャッシュは含みません。
- ソースリポジトリでは`demo/4D Invoice/Project/4D Invoice.4DProject`を開きます。付属の`Invoices_empty.4DD`は原資料として保存しており、配布ZIPには含めていません。
- 起動時は日本語を指定し、メインウィンドウを開きます。顧客がない場合は、サンプルデータの読み込み確認を表示します。
- 日本語・英語・ドイツ語・フランス語・スペイン語のリソースを`Resources/<lang>.lproj/`に保持しています。日本語起動はOSの表示言語とは独立しています。
- 4D本体や必要なコンポーネントは別途用意してください。

### デモデータ

日本語用の顧客データは、デモとスクリーンショット用に用意した固定の架空顧客200件です。
実在の法人・住所・連絡先ではなく、郵便番号`0000000`もダミー値です。
ファイルは`Resources/ja.lproj/Clients.txt`にあり、元の11列のタブ区切り形式を維持しています。
電話・携帯電話・FAX・メール・担当者は空欄です。

元の英語データと240件の商品参照、税率などの原デモの前提は維持しています。
商品価格・請求書・日付などは従来のデモ処理で生成されるため、実行ごとに変わる場合があります。
会社情報や取引は説明用であり、日本の会計・税務処理の実装例ではありません。
詳細は[データの説明](data/ja/README.md)を参照してください。

## 原文・原デモとの違い

- 本文とデモのUIを日本語化しています。本文のプログラムコードは英語原文と同一です。デモの実装には日本語リソースの参照や起動処理の変更があるため、本文のコード例と逐語的には一致しません。
- 顧客サンプルを架空の日本語データへ置き換えています。
- 図04〜16は日本語画面のキャプチャへ置き換えています。原デモが付属していない図01〜03は英語のままです。英語の元画像と元PDFは変更していません。
- スクリーンショットは現在のmacOS・4Dの画面であり、原文の画面とテーマ、配置、縦横比が異なります。
- 一部のネイティブキャプチャでCoreTextのフォントフォールバック警告を確認しています。レビュー済みの外観を採用していますが、すべてのコントロールのフォント解決を保証するものではありません。
- Write Proを含むヘッドレス試行は異常終了したため、請求書エディターやWrite Proのすべての操作・描画を検証済みとはしていません。

## 編集と再生成

PDFはMarkdownと画像から生成します。元PDFを直接編集しないでください。

| ファイル | 内容 |
|---|---|
| `src/ja.md` | 日本語本文。プログラムコードは変更しないでください。 |
| `src/en.md` | 英語原文の抽出結果。日本語本文とブロック順をそろえています。 |
| `figures/fig-NN.png` | 変更せず保存する英語の元画像。 |
| `figures/fig-NN-ja.png` | 日本語画面の置き換え画像。 |
| `figures/layout/fig-NN.json` | 配置設定。`replace`で置き換え画像を指定します。 |
| `glossary.md` | 用語集。 |

```sh
git submodule update --init .agents
make setup
make                 # チェック、図の生成、日本語PDFの生成
make check           # プログラムコードと図の参照を照合
make review          # build/contact-N.pngで元画像と比較
make release-assets  # PDFとコミット済みのデモソースZIPを生成
```

Python 3、Google Chrome、日本語フォントが必要です。再抽出にはTesseractも使用します。
macOSではヒラギノ、LinuxではNoto CJKを使用するため、生成環境により組版が多少異なります。
詳しい作業手順は[ローカライズ用テンプレート](https://github.com/miyako/4d-technote-localisation-template)を参照してください。

## 原著・制作環境

- 原著：Thomas Maul（4D Germany）、*Single Window App – Modernize your application*、Technical Note 24-14。
- 付属デモ：原テクニカルノートに付属する4D Invoice。元のソースとリソースを基にしています。
- 制作環境：[4d-technote-localisation-template](https://github.com/miyako/4d-technote-localisation-template)。
