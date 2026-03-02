---
name: pre-publish-audit
description: Audit codebases and projects before public release. Detect personal information, credentials, organization/product names, environment-specific paths, hardcoded configurations, and non-generic code patterns. Use when publishing repositories to GitHub, preparing OSS releases, reviewing code for public sharing, or checking that a project contains no private/internal references. Also use when user mentions 公開前チェック, セキュリティ監査, or OSS公開準備.
---

# Pre-Publish Audit

コードベースを公開リポジトリにリリースする前に、機密情報・個人情報・環境固有情報を検出し、汎用性を検証する監査スキル。

## 監査の実行方法

### 基本フロー

```
1. 対象ディレクトリの特定
2. ファイル一覧の収集（バイナリ・生成物を除外）
3. 各カテゴリの検査を実行
4. 監査レポートを生成
```

### トリガー例

- 「このリポジトリを公開したい」
- 「OSSとしてリリースする前にチェックして」
- 「公開前の監査をお願い」
- 「my-project を公開する準備」

## 監査カテゴリ

全6カテゴリで検査を実施する。各カテゴリは独立しており、ユーザーが特定カテゴリのみの検査を依頼した場合はそれに従う。

### Category 1: 個人情報（Personal Information）

個人を特定できる情報や、開発者のローカル環境に紐づく情報。

**検出対象:**

| パターン | 例 | 重要度 |
|----------|-----|--------|
| ローカルユーザーパス | `/Users/developer/`, `/home/dev/` | CRITICAL |
| メールアドレス | `dev@company.com` | HIGH |
| 電話番号 | `090-1234-5678` | HIGH |
| 日本の郵便番号 | `〒100-0001` | MEDIUM |
| 個人名・ハンドルネーム | コミットログ外の個人名 | MEDIUM |
| IPアドレス | `192.168.1.100`, `10.0.0.5` | MEDIUM |

**検査方法:**
1. Grepで正規表現パターンマッチ
2. パス文字列を意味的に分析（テンプレートやドキュメントの例示は除外）
3. README/ドキュメント内の「作者」「連絡先」セクションを確認

**判定基準:**
- コード内のリテラル文字列 → CRITICAL（即修正）
- コメント内 → HIGH（修正推奨）
- ドキュメント内の意図的な記載（LICENSE, CONTRIBUTORS） → OK（除外）

### Category 2: 認証情報・シークレット（Credentials & Secrets）

APIキー、トークン、パスワード等の機密情報。

**検出対象:**

| パターン | 正規表現 | 重要度 |
|----------|---------|--------|
| 汎用APIキー変数 | `(api_key\|apikey\|secret_key\|access_token\|auth_token)\s*[:=]` | CRITICAL |
| OpenAI APIキー | `sk-[a-zA-Z0-9]{10,}` | CRITICAL |
| GitHub PAT | `ghp_[a-zA-Z0-9]{36}`, `github_pat_` | CRITICAL |
| AWS Access Key | `AKIA[0-9A-Z]{16}` | CRITICAL |
| Slack トークン | `xox[bpas]-[a-zA-Z0-9-]+` | CRITICAL |
| Azure/MS トークン | `eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}` (JWT) | CRITICAL |
| パスワードリテラル | `(password\|passwd\|pwd)\s*[:=]\s*['"]` | CRITICAL |
| Base64エンコード疑い | 高エントロピー文字列（40文字以上） | MEDIUM |

**検査方法:**
1. 正規表現パターンマッチ
2. `.env`, `.env.local`, `credentials.json` 等の設定ファイルの存在確認
3. `.gitignore` に機密ファイルが含まれているか確認
4. git履歴内の過去コミットに機密情報がないか（`git log -p` でサンプル確認）

**判定基準:**
- 実際の値が含まれる → CRITICAL（即修正、git履歴からも除去が必要）
- プレースホルダー（`YOUR_API_KEY_HERE`） → OK
- 環境変数参照（`process.env.API_KEY`） → OK

### Category 3: 組織・企業情報（Organization Information）

社名、内部プロジェクト名、クライアント名等の組織固有情報。

**検出対象:**

| パターン | 例 | 重要度 |
|----------|-----|--------|
| 社名・ブランド名 | 社内利用の固有名詞 | HIGH |
| 内部プロジェクト名 | 社内コードネーム | HIGH |
| クライアント名 | 取引先の社名 | CRITICAL |
| 内部ドメイン | `*.internal.company.com` | HIGH |
| 社内Slack/Teams参照 | チャンネル名、ワークスペース名 | MEDIUM |
| Jira/Confluence参照 | `PROJ-123`, 社内Wiki URL | MEDIUM |

**検査方法:**
1. 設定ファイル（`security-check.conf`等）からの既知パターン照合
2. コード内のコメント・文字列リテラルの意味的分析
3. URLパターンの分析（内部ツール、VPN、イントラネット）
4. package.json / manifest.json の `author`, `repository` フィールド確認

**判定基準:**
- コード・コメント内の社名 → HIGH（汎用化が必要）
- LICENSE/COPYRIGHTの社名 → OK（公開に必要）
- README内のクレジット → OK（意図的な開示）

### Category 4: 製品・サービス固有情報（Product-Specific Information）

公開したくない製品名、内部API仕様、ビジネスロジック。

**検出対象:**

| パターン | 例 | 重要度 |
|----------|-----|--------|
| 内部API エンドポイント | `https://api.internal.example.com/v1/` | HIGH |
| 製品固有の設定値 | ハードコードされた閾値、ID | MEDIUM |
| ビジネスロジックコメント | 「○○の要件に基づき...」 | MEDIUM |
| 内部サービス名 | マイクロサービス名、内部ツール名 | HIGH |
| テストデータ | 実在する顧客データを含むフィクスチャ | CRITICAL |

**検査方法:**
1. URL文字列の分析（`localhost`, 内部ドメイン、非公開API）
2. コメント内の日本語テキストの意味的分析
3. テストデータ・フィクスチャファイルの内容確認
4. 設定ファイル内のハードコード値の確認

### Category 5: 環境固有情報（Environment-Specific Information）

特定の開発環境やインフラに依存する情報。

**検出対象:**

| パターン | 例 | 重要度 |
|----------|-----|--------|
| 絶対パス | `/opt/company/app/`, `C:\Projects\` | HIGH |
| ハードコードポート | `localhost:3000`, `127.0.0.1:8080` | MEDIUM |
| 固有のDB接続文字列 | `mongodb://prod-server:27017/` | CRITICAL |
| 固有のホスト名 | `prod-server-01.internal` | HIGH |
| CI/CD固有設定 | 社内Jenkins/GitLab URLなど | MEDIUM |
| OS固有パス | `C:\Users\`, `/var/log/app/` | MEDIUM |

**検査方法:**
1. パス文字列のパターンマッチ（絶対パス検出）
2. URL/ホスト名の意味的分析
3. Docker/docker-compose設定の確認
4. CI設定ファイル（`.github/workflows/`, `.gitlab-ci.yml`）の確認

**判定基準:**
- 環境変数で外部化済み → OK
- `example.com` 等のRFC準拠のダミー値 → OK
- 実環境の値がハードコード → HIGH/CRITICAL

### Category 6: 汎用性・ポータビリティ（Genericity & Portability）

コードが特定環境に依存せず、他者が利用できる状態か。

**検査項目:**

| チェック項目 | 内容 | 重要度 |
|-------------|------|--------|
| README/ドキュメント | セットアップ手順が記載されているか | HIGH |
| 環境変数の文書化 | 必要な環境変数が `.env.example` 等で示されているか | HIGH |
| 依存関係の明示 | `package.json`, `requirements.txt` が最新か | MEDIUM |
| ライセンス | LICENSE ファイルが存在するか | HIGH |
| `.gitignore` | 適切なファイルが除外されているか | MEDIUM |
| ハードコード排除 | 設定値が外部化されているか | MEDIUM |
| プラットフォーム互換 | OS固有のコマンド（`pbcopy`, `open`）がないか | LOW |
| 文字コード | UTF-8で統一されているか | LOW |

## 監査の実行手順

### Step 1: 対象ディレクトリの確認

```
ユーザーが指定したディレクトリ、またはカレントディレクトリを対象とする。
```

- `ls` でディレクトリ構造を把握
- `.gitignore` の内容を確認し、除外対象を理解
- `git log --oneline -5` で最近の変更を確認

### Step 2: ファイル収集と除外

以下のファイルは検査対象から**除外**:

```
# バイナリ・メディア
*.png, *.jpg, *.jpeg, *.gif, *.ico, *.svg, *.pdf, *.woff, *.woff2, *.ttf

# 生成物・依存関係
node_modules/, dist/, build/, .git/, __pycache__/, *.pyc, .next/

# パッケージロックファイル（生成物だが依存関係は確認）
package-lock.json, yarn.lock, pnpm-lock.yaml
```

### Step 3: カテゴリ別検査

各カテゴリについて、Grep toolとRead toolを使って検査する。

**効率的な検査順序:**

1. **Category 2（認証情報）** — 最も危険。最優先で検査
2. **Category 1（個人情報）** — 次に危険
3. **Category 3（組織情報）** — 公開時のリスク
4. **Category 4（製品情報）** — ビジネスリスク
5. **Category 5（環境固有）** — 動作に影響
6. **Category 6（汎用性）** — 品質向上

**並列検査**: Category 1-5 は独立しているため、Grep toolを並列で呼び出して効率化する。

### Step 4: 意味的分析

パターンマッチでは検出できない問題を、ファイル内容を読んで意味的に分析する。

- コメント内の日本語テキスト（社内用語、プロジェクト固有の文脈）
- テストデータの実在性（ダミーデータか実データか）
- ビジネスロジックの機密性
- README/ドキュメントの内部参照

### Step 5: 監査レポート生成

以下の形式でレポートを出力する:

```markdown
# Pre-Publish Audit Report

**対象**: {リポジトリ名}
**監査日**: {YYYY-MM-DD}
**検査ファイル数**: {N}件

## サマリー

| カテゴリ | CRITICAL | HIGH | MEDIUM | LOW |
|----------|----------|------|--------|-----|
| 個人情報 | 0 | 1 | 2 | 0 |
| 認証情報 | 1 | 0 | 0 | 0 |
| 組織情報 | 0 | 2 | 1 | 0 |
| 製品情報 | 0 | 0 | 1 | 0 |
| 環境固有 | 0 | 1 | 3 | 0 |
| 汎用性   | 0 | 1 | 0 | 2 |

## 検出結果

### CRITICAL（公開前に必ず修正）

1. **[C2-001] AWS Access Key detected**
   - ファイル: `config/aws.js:15`
   - 内容: `AKIA1234567890ABCDEF`
   - 修正案: 環境変数 `AWS_ACCESS_KEY_ID` に置換

### HIGH（修正を強く推奨）

...

### MEDIUM（確認推奨）

...

## 修正チェックリスト

- [ ] CRITICAL: {件数}件を修正
- [ ] HIGH: {件数}件を修正
- [ ] git履歴から機密情報を除去（`git filter-branch` or BFG Repo-Cleaner）
- [ ] `.gitignore` の確認
- [ ] LICENSE ファイルの確認
- [ ] README のセットアップ手順確認
```

## 既存ツールとの連携

### public-repo-security-check.sh（hookスクリプト）との関係

既存のhookスクリプトはファイル単位の正規表現チェック。本スキルは:

- **リポジトリ全体**を横断的に分析
- **意味的分析**でパターンマッチでは見つからない問題を検出
- **レポート形式**で全体像を把握可能
- **修正ガイダンス**を提供

hookは自動的に動作する「ガードレール」、本スキルは公開前の「総合検査」として併用する。

### skill-scanner との関係

`skill-scanner`（cisco-ai-skill-scanner）はAgent Skillsのセキュリティに特化。本スキルは:

- 一般的なコードベース全般が対象
- 機密情報・個人情報の検出に注力
- 汎用性・ポータビリティの検証を含む

Agent Skillsを公開する場合は、**本スキル → skill-scanner** の順で実行を推奨。

## 検査時の注意事項

### 誤検知（False Positive）への対処

以下は誤検知の可能性が高い。レポートでは「要確認」として報告し、ユーザーに判断を委ねる:

- `example.com`, `test@example.com` 等のRFC準拠ダミー値
- ドキュメント内の説明用サンプルコード
- LICENSE, CONTRIBUTORS ファイル内の個人名
- テストコード内のモック値（`mock-api-key-12345`）
- `.env.example` 内のプレースホルダー

### git履歴の重要性

ファイルから機密情報を削除しても、**git履歴には残る**。CRITICALな検出があった場合は、必ず以下を案内:

1. `git filter-branch` または BFG Repo-Cleaner での履歴書き換え
2. GitHub の secret scanning alerts の有効化
3. 漏洩したキーの即時ローテーション

## 詳細リファレンス

検出パターンの正規表現一覧と修正例は [detection-patterns.md](references/detection-patterns.md) を参照。
