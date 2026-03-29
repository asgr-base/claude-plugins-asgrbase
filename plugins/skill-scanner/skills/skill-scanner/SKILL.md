---
name: skill-scanner
description: Scan Agent Skills (SKILL.md packages) for security threats: prompt injection, data exfiltration, malicious code, command injection. Use when reviewing third-party skills before installation, auditing existing skills, or integrating security checks into CI/CD.
version: 1.0.0
author: asgr-base
createDate: 2026-03-02
updateDate: 2026-03-02
license: Apache-2.0
disable-model-invocation: true
---

# skill-scanner

Cisco AI Defense製のセキュリティスキャナー。Agent Skillsをスキャンし、プロンプトインジェクション・データ窃取・悪意あるコードを検出する。

## インストール

```bash
# uv tool（推奨・グローバルにインストール）
uv tool install cisco-ai-skill-scanner

# pip
pip install cisco-ai-skill-scanner

# 動作確認
uv run --with cisco-ai-skill-scanner skill-scanner --version
```

## 基本スキャン（コアエンジンのみ・APIキー不要）

```bash
# 単一スキルをスキャン（static + bytecode + pipeline）
uv run --with cisco-ai-skill-scanner skill-scanner scan /path/to/skill

# 振る舞い解析を追加（データフロー分析）
uv run --with cisco-ai-skill-scanner skill-scanner scan /path/to/skill --use-behavioral

# ディレクトリ内の全スキルをスキャン
uv run --with cisco-ai-skill-scanner skill-scanner scan-all /path/to/skills --recursive
```

## 高精度スキャン（LLM解析・APIキー必要）

```bash
export SKILL_SCANNER_LLM_API_KEY="your_api_key"
export SKILL_SCANNER_LLM_MODEL="claude-sonnet-4-20250514"  # または openai モデル

# LLM + メタ解析（偽陽性フィルタリング）
uv run --with cisco-ai-skill-scanner skill-scanner scan /path/to/skill \
  --use-behavioral --use-llm --llm-provider anthropic --enable-meta

# LLMを3回実行し多数決（精度向上）
uv run --with cisco-ai-skill-scanner skill-scanner scan /path/to/skill \
  --use-llm --llm-consensus-runs 3
```

## アナライザー一覧

| アナライザー | 説明 | APIキー |
|-------------|------|---------|
| static | YAML + YARAパターンマッチ | 不要 |
| bytecode | .pycファイル整合性検証 | 不要 |
| pipeline | シェルコマンドのtaint分析 | 不要 |
| behavioral | ASTデータフロー解析（Python） | 不要 |
| trigger | スキルdescriptionの曖昧さ検出 | 不要 |
| llm | セマンティック解析（SKILL.md + スクリプト） | 必要 |
| meta | 偽陽性フィルタリング（llm結果の精査） | 必要 |
| virustotal | バイナリファイルのハッシュ照合 | 必要 |
| aidefense | Cisco AI Defenseクラウド解析 | 必要 |

## 出力フォーマット

```bash
# Markdownレポート（人間向け）
skill-scanner scan /path/to/skill --format markdown --detailed --output report.md

# JSON（CI/CD連携）
skill-scanner scan /path/to/skill --format json --output results.json

# SARIF（GitHub Code Scanning）
skill-scanner scan /path/to/skill --format sarif --output results.sarif

# HTMLインタラクティブレポート
skill-scanner scan /path/to/skill --use-llm --enable-meta --format html --output report.html

# テーブル形式（ターミナル表示）
skill-scanner scan-all /path/to/skills --format table
```

## スキャンポリシー

```bash
# プリセット（strict / balanced / permissive）
skill-scanner scan /path/to/skill --policy strict

# カスタムポリシー生成
skill-scanner generate-policy -o my_policy.yaml

# インタラクティブポリシー設定TUI
skill-scanner configure-policy
```

## CI/CDゲート

```bash
# HIGH以上で終了コード1（ビルド失敗）
skill-scanner scan-all ./skills --fail-on-severity high --format sarif --output results.sarif

# スキル間の重複検出
skill-scanner scan-all ./skills --recursive --check-overlap
```

## 検出する脅威カテゴリ

| 脅威 | 説明 |
|------|------|
| プロンプトインジェクション | 指示の上書き・間接インジェクション |
| データ窃取 | 外部サーバーへのHTTP POST、環境変数の盗取 |
| コマンドインジェクション | evalや危険な実行プリミティブ |
| 難読化 | 検出回避のためのエンコーディング |
| ハードコードされたシークレット | 埋め込まれたAPIキー・認証情報 |
| サプライチェーン攻撃 | 悪意あるパッケージの注入 |
| ツールポイズニング | ツールの動作改ざん |

詳細: [references/analyzers.md](references/analyzers.md) | [references/troubleshooting.md](references/troubleshooting.md)

## 注意事項

- `No findings` はスキルが安全であることを**保証しない**（既知パターンの不検出を意味する）
- 高リスクスキルは自動スキャンに加え**手動コードレビュー**を推奨
- LLMアナライザーなしでも静的解析・振る舞い解析は有効

## 参考リンク

- [GitHub - cisco-ai-defense/skill-scanner](https://github.com/cisco-ai-defense/skill-scanner)
- [PyPI - cisco-ai-skill-scanner](https://pypi.org/project/cisco-ai-skill-scanner/)
- [Cisco AI Security Framework](https://learn-cloudsecurity.cisco.com/ai-security-framework)
