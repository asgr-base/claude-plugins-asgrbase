# claude-insight-reflect

Claude Code Insightレポートを生成・翻訳・分析し、示唆をプロジェクト設定（CLAUDE.md）に反映するスキル。

## 概要

Claude Codeの `/insights` レポートを自動生成し：
- 日本語に翻訳
- 改善提案を抽出
- プロジェクト設定ファイル（CLAUDE.md）に反映
- 関連スキルのSKILL.mdを更新

これにより、**使用パターンの分析 → ルールの改善**というフィードバックループを構築できます。

## レポート生成

> `/insights` はビルトインスラッシュコマンドですが、`CLAUDECODE= claude -p "/insights"` でBashから生成可能です。
> レポートが存在しない場合、スキルが自動的に生成します。

## 機能

| 機能 | 説明 |
|------|------|
| レポート生成 | `CLAUDECODE= claude -p "/insights"` でレポートを自動生成 |
| レポート翻訳 | 英語レポートを日本語に翻訳 |
| 示唆抽出 | 「試すべき機能」「カスタムスキル」等のセクションから改善点を特定 |
| CLAUDE.md更新 | 汎用ルールをプロジェクト設定に追加 |
| スキル更新 | スキル固有の改善を該当SKILL.mdに反映 |

## インストール

### 方法1: ディレクトリをコピー

```bash
cp -r claude-insight-reflect ~/.claude/skills/
```

### 方法2: シンボリックリンク

```bash
ln -s /path/to/claude-insight-reflect ~/.claude/skills/claude-insight-reflect
```

## 使用方法

### 基本的な使い方

```
/claude-insight-reflect
```

ワークフロー：

1. **レポート生成**: 当日レポートがなければ自動生成（`CLAUDECODE= claude -p "/insights"`）
2. **アーカイブ**: プロジェクト配下に日付付きでコピー
3. **翻訳**: 英語レポートを日本語に翻訳
4. **示唆分析**: レポートから改善提案を抽出
5. **反映確認**: ユーザーに反映する項目を確認
6. **ファイル更新**: CLAUDE.mdまたは関連SKILL.mdを更新

### オプション

```
/claude-insight-reflect --generate-only   # レポート生成のみ
/claude-insight-reflect --translate-only  # レポート翻訳のみ
/claude-insight-reflect --apply-only      # 既存レポートから示唆反映のみ
```

## 前提条件

- `claude` コマンドがPATH上で利用可能であること
- プロジェクトに `CLAUDE.md` が存在
- レポート保存用の `.claude/usage-data/` ディレクトリ

## ディレクトリ構造

```
~/.claude/usage-data/
└── report.html                    # /insights が生成（ソース）

.claude/usage-data/
├── report-YYYYMMDD.html           # 日付アーカイブ（英語）
└── report-YYYYMMDD-ja.html        # 日本語翻訳版
```

## ライセンス

MIT License
