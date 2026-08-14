# UNAGITANI Corporate Site

株式会社UNAGITANIの静的コーポレートサイトです。外部ライブラリを使用しません。

## ローカル確認

プロジェクト直下で次を実行します。

```bash
python3 -m http.server 8000
```

`http://localhost:8000/` を開きます。終了は `Ctrl+C` です。

## 更新方法

- 各ページの文章: 該当する `*/index.html`
- 共通デザイン: `assets/css/style.css`
- 最小限の動作: `assets/js/main.js`
- 理念候補などの管理文言: `assets/js/site-data.js`
- お知らせ: `news/index.html`（事実確認後にのみ追加）

更新後はPC・スマホ幅で確認し、リンク、title、description、OGP、構造化データを確認してください。未確定事項は `docs/CONTENT_REVIEW.md` で管理します。

## 公開方法

静的ホスティングに全ファイルを配置し、`corporate.unagitani.com` を割り当てます。公開前にDNS設定、HTTPS、HTTPからHTTPSへのリダイレクト、フォーム送信先、OGP画像、プライバシーポリシーの最終確認を行ってください。特定のホスティング事業者・フォームサービスはこのリポジトリでは契約・設定していません。

## SEO・Google Search Console

公開URLは `https://corporate.unagitani.com/` です。`robots.txt` と `sitemap.xml` は次のURLで公開します。

- https://corporate.unagitani.com/robots.txt
- https://corporate.unagitani.com/sitemap.xml

本番の基本SEO監査は、リポジトリ直下で次の1コマンドを実行します。このスクリプトはCorporateと鰻谷饅頭の両サイトについて、HTTP、title、description、canonical、h1、noindex、JSON-LD、robots、sitemap、内部リンクを確認します。

```bash
python3 scripts/seo_check.py
```

Search Consoleの所有権確認でHTML verification fileを選んだ場合は、Googleからダウンロードした `googleXXXXXXXXXXXXXXXX.html` を内容・ファイル名を変えずこのリポジトリのルートへ配置し、デプロイ後に `https://corporate.unagitani.com/googleXXXXXXXXXXXXXXXX.html` が200で取得できることを確認します。HTMLタグ方式の場合は、Google指定の `google-site-verification` metaタグをトップページの `<head>` に追加します。検証用トークンを架空値で公開しないでください。

コードのデプロイ完了後、森さんが次を実施してください。

1. Google Search Consoleへ `https://corporate.unagitani.com/` のURLプレフィックスプロパティを追加する
2. HTMLファイルまたはHTMLタグで所有権を確認する
3. `https://corporate.unagitani.com/sitemap.xml` を送信する
4. URL検査で `https://corporate.unagitani.com/` を検査する
5. 「インデックス登録をリクエスト」を実行する
6. `/about/`、`/business/`、`/brands/`、`/message/`、`/company/`、`/news/`、`/contact/`、`/privacy/` も必要に応じてURL検査する

サイトマップ送信や登録リクエストはインデックスを保証するものではありません。掲載可否と反映時期は検索エンジンが判断します。
