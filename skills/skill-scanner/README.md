# skill-scanner

Agent Skillsのセキュリティスキャナー。プロンプトインジェクション・データ窃取・悪意あるコードパターンを検出する。

## What It Does

[Cisco AI Defense製 skill-scanner](https://github.com/cisco-ai-defense/skill-scanner) を Claude Code から利用するためのスキル。サードパーティスキルのインストール前レビューや、既存スキルの定期監査、CI/CDへのセキュリティゲート組み込みに使用する。

## Key Features

- **多層検出エンジン** — 静的解析・バイトコード・パイプライン・振る舞い解析・LLMセマンティック解析
- **偽陽性フィルタリング** — メタアナライザーによるノイズ低減
- **脅威タクソノミー** — Cisco AI Security Framework準拠（AITech/AISubtech コード）
- **複数出力形式** — summary / json / markdown / sarif / html / table
- **CI/CD対応** — `--fail-on-severity` で終了コード制御、SARIF出力でGitHub Code Scanning連携

## Usage

```
/skill-scanner
```

スキャン対象のパスを伝えるだけでスキャンを実行する。

## Examples

```bash
# 単一スキル（コアエンジンのみ）
skill-scanner scan .claude/skills/my-skill

# 振る舞い解析あり
skill-scanner scan .claude/skills/my-skill --use-behavioral

# LLM解析 + 偽陽性フィルタ（高精度）
SKILL_SCANNER_LLM_API_KEY="..." skill-scanner scan .claude/skills/my-skill \
  --use-behavioral --use-llm --llm-provider anthropic --enable-meta

# ディレクトリ一括スキャン（CI/CDゲート）
skill-scanner scan-all .claude/skills --recursive --fail-on-severity high
```

## File Structure

```
skill-scanner/
├── SKILL.md                    # メイン（インストール・基本操作・コマンドリファレンス）
└── references/
    ├── analyzers.md            # アナライザー詳細・推奨構成・脅威タクソノミー
    └── troubleshooting.md      # よくある問題と解決策
```

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)（推奨）または pip
- LLMアナライザー使用時: Anthropic または OpenAI APIキー

## Installation

```bash
uv tool install cisco-ai-skill-scanner
```

## License

Apache 2.0
