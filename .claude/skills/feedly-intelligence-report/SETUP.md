# セットアップガイド

## 1. Feedly Access Token 取得

トークン取得には2つの方法があります。

### 方法A: 自動取得スクリプト（推奨）

Playwrightを使ってブラウザからトークンを自動取得します。

```bash
# Chromiumインストール（初回のみ）
uv run --with playwright python -m playwright install chromium

# トークン取得
uv run --with playwright --with requests python scripts/feedly_token_refresh.py
```

ブラウザが開き、Feedlyにアクセスします：
- **ログイン済み**: 自動的にトークンを取得
- **未ログイン**: ログイン画面が表示されるので手動でログイン

トークンは `~/.feedly/token` に保存されます。

**オプション**:
| オプション | 説明 |
|------------|------|
| `--check` | 現在のトークンの有効性を確認 |
| `--force` | 既存トークンが有効でも強制更新 |
| `--output PATH` | 出力先を指定 |

### 方法B: 手動取得（ブラウザコンソール）

1. https://feedly.com にログイン
2. 開発者ツールを開く（F12）
3. Consoleタブで以下を実行:

```javascript
JSON.parse(localStorage.getItem('feedly.session')).feedlyToken
```

4. 表示されたトークンをコピーして保存:

```bash
mkdir -p ~/.feedly
echo 'YOUR_TOKEN_HERE' > ~/.feedly/token
chmod 600 ~/.feedly/token
```

### 方法C: Developer Token（Pro plan必要）

> ⚠️ 2026年1月以降、Developer Tokenの発行にはPro plan（有料）が必要です。

1. https://feedly.com/v3/auth/dev にアクセス
2. 「Generate Token」をクリック
3. トークンをコピーして保存

### トークンの制限事項

| 項目 | Web Access Token | Developer Token |
|------|------------------|-----------------|
| 有効期限 | 約1週間 | 3ヶ月 |
| 取得方法 | ブラウザ/スクリプト | Pro plan必要 |
| リクエスト上限 | 月間100,000 | 月間100,000 |
| 用途 | 個人利用のみ | 個人利用のみ |

## 2. Feedlyカテゴリの準備

### Feedly Webでカテゴリ作成

1. https://feedly.com にログイン
2. 左サイドバーの「+ Create Feed」をクリック
3. カテゴリ名を入力（例: Tech, Business）
4. RSSフィードを追加

### Stream IDの確認

**方法1: URLから取得**

1. Feedly Webで目的のカテゴリをクリック
2. URLをコピー:
   ```
   https://feedly.com/i/category/user/xxxx-xxxx-xxxx/category/MyCategory
                                   └─────────────── Stream ID ───────────────┘
   ```

**方法2: API経由で取得**

```bash
curl -s -H "Authorization: Bearer $(cat ~/.feedly/token)" \
     "https://api.feedly.com/v3/categories" | jq '.[].id'
```

## 3. 設定ファイルの作成

### サンプルをコピー

```bash
# スキルディレクトリから設定フォルダにコピー
cp /path/to/skill/config-sample.json ~/.feedly/config.json

# エディタで編集
vi ~/.feedly/config.json
```

### 最低限の設定

```json
{
  "token_file": "~/.feedly/token",
  "output_dir": "Project/FeedlyReports",
  "categories": [
    {
      "name": "あなたのカテゴリ名",
      "slug": "your-category",
      "stream_id": "user/YOUR_USER_ID/category/YourCategory",
      "keywords": ["関連キーワード1", "関連キーワード2"]
    }
  ]
}
```

詳細な設定項目は [CONFIG.md](CONFIG.md) を参照。

## 4. Python依存関係

```bash
pip install requests
```

## 5. 動作確認

```bash
# トークン確認
cat ~/.feedly/token | head -c 20
echo "..."

# API疎通確認
curl -s -H "Authorization: Bearer $(cat ~/.feedly/token)" \
     "https://api.feedly.com/v3/profile" | jq .email

# スクリプトテスト
python /path/to/skill/scripts/feedly_fetch.py --test

# 記事取得テスト
python /path/to/skill/scripts/feedly_fetch.py \
    --config ~/.feedly/config.json \
    --output /tmp/test_articles.json
```

## トラブルシューティング

| エラー | 原因 | 対処 |
|--------|------|------|
| 401 Unauthorized | トークン無効/期限切れ | トークン再取得 |
| 403 Forbidden | API権限なし | Developer Token使用確認 |
| 429 Too Many Requests | レート制限 | 時間を空けて再試行 |
| Stream not found | Stream ID誤り | カテゴリ確認 |
| Config file not found | 設定ファイルなし | `~/.feedly/config.json` を作成 |

## セキュリティ注意事項

- トークンファイルの権限は `600` に設定
- トークンをGitにコミットしない
- `.gitignore` に以下を追加:
  ```
  ~/.feedly/
  **/token
  **/config.json
  ```

---

**Last Updated**: 2026-02-03
