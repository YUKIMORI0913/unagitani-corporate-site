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

静的ホスティングに全ファイルを配置し、`unagitani.co.jp` を割り当てます。公開前にDNS設定、HTTPS、フォーム送信先、OGP画像、プライバシーポリシーの最終確認を行ってください。特定のホスティング事業者・フォームサービスはこのリポジトリでは契約・設定していません。
