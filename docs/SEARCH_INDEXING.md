# 検索インデックス運用（corporate / manju 共通）

2サイトとも公開は2026年8月中旬、更新は9月。しかし9月下旬時点でGoogle検索に
どちらも出てきません。この文書は、その原因として確認できた事実、コード側で
実施した対策、そして人が実施する必要がある作業を記録します。

## 確認できた事実（2026-09-23）

| 項目 | corporate.unagitani.com | manju.unagitani.com |
| --- | --- | --- |
| DNS | GitHub Pages を正しく参照 | GitHub Pages を正しく参照 |
| robots.txt | `Allow: /` ＋ sitemap宣言 | `Allow: /` ＋ sitemap宣言 |
| noindex | なし | なし |
| canonical / OGP / 構造化データ | あり | あり |
| Search Console登録の記録 | なし | 2026-08-14 実施済み |
| 検索結果 | 法人データベースのみ表示 | 旧Wixサイトが表示 |

つまり「Googleに拒否されている」のではなく、**Googleにまだ登録されていない**
状態です。

## 原因1: Search Consoleの所有権確認タグが2サイトで同一

`corporate.unagitani.com` と `manju.unagitani.com` の `<head>` に、同じ
`google-site-verification` の値が入っていました（どちらも2026-08-14の
コミットで追加）。

HTMLタグ方式のトークンはプロパティごとに発行されるため、同じ値を別ホストへ
貼っても所有権は確認できません。記録が残っているのは鰻谷饅頭サイトだけなので、
コーポレートサイトのプロパティは未確認、つまりサイトマップ送信もインデックス
登録リクエストも届いていない可能性が高いです。

**対策（人の作業）**: `unagitani.com` の **ドメインプロパティ** をDNSのTXT
レコードで確認します。サブドメインとhttp/httpsをまとめてカバーでき、HTMLタグの
重複問題も解消します。手順は下の「お名前.comでの作業」を参照してください。

## 原因2: 本文がJavaScriptでしか生成されていなかった

Googleが最初に取得する生のHTMLに、次の内容が含まれていませんでした。

- コーポレートサイト: 会社概要の全項目（商号・代表者・所在地・古物商許可ほか）、
  売上高、沿革。`assets/js/main.js` がブラウザ上で組み立てていた
- 鰻谷饅頭サイト: トップページの写真5枚と Photo Archive の一覧（208枚）。
  `photos.json` を読むJavaScriptが組み立てていた

Googleはレンダリングも行いますが、後回しのキューに入ります。被リンクのない
新規ドメインではレンダリング前の評価で「内容の薄いページ」と判断され、
「検出 — インデックス未登録」「クロール済み — インデックス未登録」になりやすい
構成でした。

**対策（実施済み）**: 生成スクリプトを追加し、同じ内容を静的HTMLへ焼き込みました。

| リポジトリ | スクリプト | 対象 |
| --- | --- | --- |
| unagitani-corporate-site | `scripts/render_static.py` | ヘッダー、フッター、会社概要、売上高、沿革、OGP |
| unagitani-corporate-site | `scripts/generate_sitemap.py` | sitemap.xml（lastmodはgitの最終コミット日） |
| yukimori0913.github.io | `scripts/render_photos.py` | トップの写真5枚、Photo Archive 1ページ目 |

どちらも `--check` を付けるとデータとHTMLの不一致を検出します。データを更新した
ときはスクリプトを実行してからコミットしてください。JavaScript側は既に内容が
あれば描画をスキップするため、二重表示にはなりません。

## 原因3: 被リンクがない

新規ドメインで外部からのリンクが1本もない状態です。サイトマップだけで発見は
されますが、インデックスされる保証はありません。

**対策（一部実施済み）**: 鰻谷饅頭サイトのフッターからコーポレートサイトへの
リンクを追加しました（逆方向は `/brands/` に既存）。また、コーポレートサイトの
フッターを全ページ網羅に変更し、どこからもリンクされていなかった `/about/` の
孤立を解消しました。

**残りは人の作業**: 下の「外部プロフィールの統一」を参照してください。

## お名前.comでの作業（ドメインプロパティのTXT確認）

1. Google Search Console を開き、左上のプロパティ選択 →「プロパティを追加」
2. 左側の **ドメイン** を選び、`unagitani.com` と入力（`https://` やサブドメインは付けない）
3. 表示される `google-site-verification=......` のTXTレコード値をコピー
4. お名前.com Navi にログイン →「ドメイン」→「DNS」→「DNSレコード設定を利用する」
5. `unagitani.com` を選び「次へ」
6. 入力欄に次を設定して「追加」
   - ホスト名: 空欄（ルート）
   - TYPE: `TXT`
   - TTL: 3600
   - VALUE: 手順3でコピーした値
7. 「確認画面へ進む」→「設定する」
8. 反映を待ってから（数分〜数時間）、Search Consoleで「確認」を押す

TXTレコードは既存のレコードを消さずに追加してください。既存のTXT（メール認証
など）と併存できます。

反映確認はターミナルからも行えます。

```bash
dig +short TXT unagitani.com
```

## Search Consoleでの作業（ドメインプロパティ確認後）

1. `unagitani.com` のドメインプロパティで、サイトマップに次の2つを送信
   - `https://corporate.unagitani.com/sitemap.xml`
   - `https://manju.unagitani.com/sitemap.xml`
2. URL検査で次を検査し、状態を確認して「インデックス登録をリクエスト」
   - `https://corporate.unagitani.com/`
   - `https://corporate.unagitani.com/company/`
   - `https://manju.unagitani.com/`
   - `https://manju.unagitani.com/gallery.html`
3. URL検査の「公開URLをテスト」→「HTMLを表示」で、会社概要や写真がHTMLに
   含まれていることを確認する（今回の対策が効いているかの確認）

状態表示の読み方:

- **URLがGoogleに登録されています** — 登録済み。あとは順位の問題
- **検出 — インデックス未登録** — 発見済みだが未クロール。被リンクと待ち時間の問題
- **クロール済み — インデックス未登録** — 内容が評価されなかった。本文量と独自性の問題
- **ページのリダイレクトがあります / 重複しています** — canonical設定の問題

## 外部プロフィールの統一（人の作業）

Googleに「このドメインが公式である」と伝えるには、本人が管理する外部プロフィール
からリンクするのが最短です。

鰻谷饅頭サイト向け:

- Instagram `@bass.you` のプロフィールURL
- X `@unagitani_913` のプロフィールURL
- YouTube `@manjuunagitani7643` のチャンネル概要
- Bandcamp、TuneCore のアーティストページ

コーポレートサイト向け:

- Amazon、楽天市場、Yahoo!ショッピング各店舗の「会社概要」「特定商取引法に基づく表記」
- 請求書、名刺、メール署名

いずれも旧Wix URL（`unagitanibass.wixsite.com`）が残っている場合は差し替えます。

## 監査コマンド

```bash
# 本番2サイトを、JavaScriptを実行せずに監査（コーポレートサイトのリポジトリ）
python3 scripts/seo_check.py

# 生成物とデータの不一致チェック
python3 scripts/render_static.py --check
python3 scripts/generate_sitemap.py --check

# 鰻谷饅頭サイトのリポジトリ
python3 scripts/render_photos.py --check
python3 scripts/check_manju_seo.py
```

## 注意

Search Consoleへの登録、サイトマップ送信、インデックス登録リクエストは、
検索結果への掲載も順位も保証しません。技術的な障害を取り除いたうえで、
再クロールを待つことになります。
