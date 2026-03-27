# Detection Patterns Reference

検出パターンの正規表現一覧と具体的な修正例。

## Category 1: 個人情報

### ローカルパス

```regex
/Users/[a-zA-Z0-9_-]+/
/home/[a-zA-Z0-9_-]+/
C:\\Users\\[a-zA-Z0-9_-]+\\
```

**修正例:**
```javascript
// Before
const config = '/Users/developer/projects/app/config.json';

// After (環境変数)
const config = path.join(process.env.HOME, 'projects/app/config.json');

// After (相対パス)
const config = path.resolve(__dirname, '../config.json');
```

### メールアドレス

```regex
[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
```

**除外対象:**
- `noreply@github.com` — GitHub標準
- `*@example.com`, `*@example.org` — RFC 2606準拠のダミー
- `user@example.com` in README/docs — 説明用サンプル

### 電話番号（日本）

```regex
0[0-9]{1,4}-[0-9]{1,4}-[0-9]{4}
\+81[0-9-]+
```

### 郵便番号（日本）

```regex
〒[0-9]{3}-[0-9]{4}
```

### プライベートIPアドレス

```regex
192\.168\.[0-9]{1,3}\.[0-9]{1,3}
10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}
172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}
```

## Category 2: 認証情報・シークレット

### 汎用キー変数

```regex
(api_key|apikey|api-key|secret_key|secret|access_token|auth_token|private_key)\s*[:=]
```

**除外条件:** 値がプレースホルダー（`YOUR_*`, `xxx`, `<placeholder>`, `${ENV_VAR}`）

### プロバイダー固有トークン

| プロバイダー | パターン |
|-------------|---------|
| OpenAI | `sk-[a-zA-Z0-9]{20,}` |
| Anthropic | `sk-ant-[a-zA-Z0-9-]{20,}` |
| GitHub PAT | `ghp_[a-zA-Z0-9]{36}` |
| GitHub OAuth | `gho_[a-zA-Z0-9]{36}` |
| GitHub Fine-grained | `github_pat_[a-zA-Z0-9_]{20,}` |
| AWS Access Key | `AKIA[0-9A-Z]{16}` |
| AWS Secret Key | `aws_secret_access_key` (variable name) |
| Slack Bot | `xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+` |
| Slack User | `xoxp-[0-9]+-[0-9]+-[0-9]+-[a-zA-Z0-9]+` |
| Slack App | `xapp-[a-zA-Z0-9-]+` |
| Google API | `AIza[0-9A-Za-z_-]{35}` |
| Azure | JWT形式 `eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+` |
| npm | `npm_[a-zA-Z0-9]{36}` |
| PyPI | `pypi-[a-zA-Z0-9]{30,}` |

### パスワード

```regex
(password|passwd|pwd)\s*[:=]\s*['"][^'"]+['"]
```

**除外条件:**
- 値が空文字列、`null`, `undefined`
- テストファイル内の既知モック値
- `.env.example` 内のプレースホルダー

### 高エントロピー文字列

40文字以上の英数字文字列で、明らかなエンコード（Base64, hex）や変数名ではないもの。

**判定指標:** Shannon entropy > 4.5 かつ長さ > 40

## Category 3: 組織・企業情報

### 内部ドメイン

```regex
[a-zA-Z0-9-]+\.(internal|local|corp|intranet)\.[a-zA-Z]+
[a-zA-Z0-9-]+\.slack\.com
[a-zA-Z0-9-]+\.atlassian\.net
```

### プロジェクト管理参照

```regex
[A-Z]{2,10}-[0-9]+                # Jira issue key
https?://[^/]+\.atlassian\.net     # Confluence/Jira URL
https?://[^/]+\.slack\.com         # Slack URL
```

### package.json / manifest.json の確認項目

```json
{
  "author": "→ 個人名が含まれていないか",
  "repository": "→ 社内リポジトリURLではないか",
  "bugs": "→ 社内issue trackerではないか",
  "homepage": "→ 社内サイトではないか",
  "contributors": "→ 公開してよい情報か"
}
```

## Category 4: 製品・サービス固有情報

### 内部APIエンドポイント

```regex
https?://api\.[a-zA-Z0-9-]+\.(internal|local|corp|dev)/
https?://[a-zA-Z0-9-]+\.execute-api\.[a-zA-Z0-9-]+\.amazonaws\.com/
localhost:[0-9]+/api/
127\.0\.0\.1:[0-9]+/api/
```

### テストデータの実在性チェック

テストデータ・フィクスチャに以下が含まれていないか:
- 実在する人名（日本人名パターン: 姓+名、カタカナ名）
- 実在する住所
- 実在する電話番号・メールアドレス
- 実在する企業名

## Category 5: 環境固有情報

### 絶対パス

```regex
^/[a-zA-Z0-9]+/[a-zA-Z0-9]+/     # Unix絶対パス
[A-Z]:\\[a-zA-Z0-9]+\\             # Windows絶対パス
```

**除外:**
- `/usr/bin/`, `/usr/local/` — 標準パス
- `/dev/null`, `/dev/stdin` — デバイスファイル
- `/tmp/` — テンポラリ（ただし固有のファイル名がある場合は注意）

### データベース接続文字列

```regex
(mongodb|mysql|postgres|redis)://[^@\s]+@[^/\s]+
jdbc:[a-zA-Z]+://[^@\s]+@[^/\s]+
```

### ハードコードされたポート

検出はするが、`3000`, `8080`, `5432` 等の標準ポートは LOW とする。
非標準ポート（`47832`等）は HIGH。

## Category 6: 汎用性チェックリスト

パターンマッチではなく、ファイルの存在・内容を確認:

| チェック | ファイル | 内容 |
|---------|--------|------|
| LICENSE | `LICENSE`, `LICENSE.md` | 存在するか、適切なライセンスか |
| README | `README.md` | セットアップ手順があるか |
| 環境変数 | `.env.example`, `.env.sample` | 必要な変数が文書化されているか |
| gitignore | `.gitignore` | `.env`, `node_modules/`, IDE設定が含まれるか |
| 依存関係 | `package.json`, `requirements.txt` | ロックファイルとの整合性 |
| CI/CD | `.github/workflows/` | 社内固有の設定がないか |
| Docker | `Dockerfile`, `docker-compose.yml` | 社内レジストリ参照がないか |

## 重要度の定義

| Level | 定義 | アクション |
|-------|------|-----------|
| **CRITICAL** | 公開すると直接的なセキュリティリスク（認証情報漏洩、個人情報漏洩） | **公開前に必ず修正**。git履歴からも除去 |
| **HIGH** | 組織情報の漏洩、プライバシーリスク | **修正を強く推奨**。ユーザー判断で除外可 |
| **MEDIUM** | 環境依存、品質上の問題 | **確認を推奨**。意図的であればOK |
| **LOW** | ベストプラクティスからの逸脱 | **参考情報**。修正は任意 |
