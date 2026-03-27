# 日本法令確認スキル（Japanese Law Verification Skill）

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Agent%20Skill-purple)](https://code.claude.com)
[![Version](https://img.shields.io/badge/version-2.1.0-green)](https://github.com/asgr-base/agent-skills/releases)

## 概要

e-Gov法令MCPサーバーを活用して、日本の法令・税法の条文を正確に検索・確認するClaude Code Agent Skillです。

## 主な機能

- 所得税法、労働基準法、会社法などの法令検索
- 特定の条文の取得と解釈
- 税務処理・社会保険・労働法の法的根拠確認
- 税制改正の内容確認

## 前提条件

### 1. e-Gov法令MCPサーバーのインストール

このスキルを使用するには、事前にe-Gov法令MCPサーバーをインストールする必要があります。

#### インストール手順（macOS）

1. **リポジトリをクローン**

```bash
git clone https://github.com/ryoooo/e-gov-law-mcp.git
cd e-gov-law-mcp
```

2. **uvパッケージマネージャーのインストール**

uvがインストールされていない場合は、先にインストールしてください:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. **依存関係をインストール**

```bash
uv sync --python 3.13
```

**注意**: Python 3.14以上では互換性の問題があるため、Python 3.13を使用してください。

### 2. Claude Code CLI へのMCP設定

#### 方法1: コマンドラインから追加（推奨）

```bash
claude mcp add e-gov-law
```

対話形式で以下を入力:
- **Command**: `/Users/YOUR_USERNAME/.local/bin/uv`（`which uv`で確認）
- **Args**: `run --directory /ABSOLUTE/PATH/TO/e-gov-law-mcp python src/mcp_server.py`

#### 方法2: 設定ファイルを直接編集

`~/.claude.json`の`mcpServers`セクションに追加:

```json
{
  "mcpServers": {
    "e-gov-law": {
      "type": "stdio",
      "command": "/Users/YOUR_USERNAME/.local/bin/uv",
      "args": [
        "run",
        "--directory",
        "/ABSOLUTE/PATH/TO/e-gov-law-mcp",
        "python",
        "src/mcp_server.py"
      ],
      "env": {}
    }
  }
}
```

**パスの確認方法**:

```bash
# uvコマンドのパス確認
which uv

# e-gov-law-mcpのパス確認
cd e-gov-law-mcp && pwd
```

### 3. 接続確認

新しいClaude Code CLIセッションを開始し、以下のコマンドで接続を確認:

```bash
claude mcp list
```

`✓ Connected` と表示されれば成功です。

**トラブルシューティング**: `✗ Disconnected`と表示される場合は、手動実行でエラーを確認:

```bash
cd /path/to/e-gov-law-mcp
uv run --python 3.13 python src/mcp_server.py
```

## 使い方

### 基本的な使用例

このスキルは、法令確認が必要な質問を受けた際に自動的に起動されます。

**例1: 源泉徴収のタイミング確認**

```
ユーザー: 給与の源泉徴収はいつ行うべきですか？

Claude: 所得税法第183条に基づいて確認します...
（e-gov-law:find_law_articleツールを使用）
```

**例2: 配偶者控除の要件確認**

```
ユーザー: 配偶者控除の所得要件を教えてください

Claude: 所得税法第83条を確認します...
（e-gov-law:find_law_articleツールを使用）
```

### 明示的にスキルを呼び出す

```
ユーザー: law-verificationスキルを使って、労働基準法第24条を確認してください
```

## トラブルシューティング

### MCPサーバーが認識されない

1. **設定ファイルのパスを確認**

   - e-gov-law-mcpのクローン先の絶対パスが正しいか確認
   - uvコマンドの絶対パスが正しいか確認（`which uv`）

2. **新しいClaude Code CLIセッションを開始**

   設定変更後は、新しいセッションで`claude mcp list`を実行して接続確認

3. **手動実行でエラーを確認**

   ```bash
   cd /path/to/e-gov-law-mcp
   uv run --python 3.13 python src/mcp_server.py
   ```

   エラーメッセージが表示される場合は、依存関係が正しくインストールされているか確認してください。

### "tool not found"エラー

**原因**: 完全修飾ツール名を使用していない

**解決策**: `e-gov-law:find_law_article`の形式でツールを呼び出してください。

```markdown
❌ 誤: find_law_article(law_name="所得税法", article_number="183")
✅ 正: e-gov-law:find_law_article(law_name="所得税法", article_number="183")
```

### Python 3.14 互換性エラー

**エラー例**: `pydantic-core build failed`

**解決策**: Python 3.13を指定してインストール:

```bash
uv sync --python 3.13
```

## 対応している法令

### 税法

- 所得税法
- 所得税法施行令
- 地方税法
- 法人税法

### 労働法

- 労働基準法
- 労働者災害補償保険法
- 雇用保険法
- 労働契約法

### 会社法・その他

- 会社法
- 民法
- 日本国憲法

## 参考資料

- [e-Gov法令MCPサーバー（LobeHub）](https://lobehub.com/ja/mcp/ryoooo-e-gov-law-mcp)
- [GitHub - ryoooo/e-gov-law-mcp](https://github.com/ryoooo/e-gov-law-mcp)
- [e-Gov法令検索](https://elaws.e-gov.go.jp/)
- [Claude Code Agent Skills](https://github.com/anthropics/skills)

## インストール方法

### 方法1: Claude Code プラグインとしてインストール（推奨）

```bash
/plugin marketplace add asgr-base/agent-skills
/plugin install jp-law-verification@asgr-agent-skills
```

### 方法2: 手動インストール

```bash
git clone https://github.com/asgr-base/agent-skills.git
cp -r agent-skills/skills/jp-law-verification ~/.claude/skills/
```

### 方法3: degit（特定フォルダのみ）

```bash
npx degit asgr-base/agent-skills/skills/jp-law-verification ~/.claude/skills/jp-law-verification
```

## バージョン情報

- **バージョン**: 2.1.0
- **作成日**: 2026-01-10
- **最終更新**: 2026-01-25
- **作成者**: asgr-base

## ライセンス

Apache License 2.0 - 詳細は [LICENSE](../../LICENSE) を参照してください。

## フィードバック・貢献

- **Issue報告**: [GitHub Issues](https://github.com/asgr-base/agent-skills/issues)
- **Pull Request**: 歓迎します！
