# ASGR Base Claude Code Plugins

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugins-purple)](https://code.claude.com)

日本の法令・税務・会計・業務効率化に特化した Claude Code プラグインコレクションです。
Agent Skills、hooks、commands、configurations を含む統合マーケットプレイスとして提供しています。

## クイックスタート

### Claude Code プラグインとしてインストール

```bash
/plugin marketplace add asgr-base/claude-plugins-asgrbase
```

### 特定のスキルをインストール

```bash
/plugin install jp-law-verification@claude-plugins-asgrbase
```

### 手動インストール

```bash
# リポジトリをクローン
git clone https://github.com/asgr-base/agent-skills.git

# 必要なスキルを ~/.claude/skills/ にコピー
cp -r agent-skills/skills/jp-law-verification ~/.claude/skills/
```

## スキル一覧

### 日本の法令・税務・会計

| スキル名 | 説明 | バージョン |
|---------|------|-----------|
| [jp-law-verification](skills/jp-law-verification/) | e-Gov法令APIで日本の法令を検索・確認 | 2.1.0 |
| [jp-etax-guide](skills/jp-etax-guide/) | e-Tax（国税電子申告）の利用ガイド | 1.0.0 |
| [jp-eltax-guide](skills/jp-eltax-guide/) | eLTAX（地方税ポータル）の利用ガイド | 2.0.0 |
| [jp-aoiro-accounting](skills/jp-aoiro-accounting/) | 青色申告帳簿をMarkdown + Pythonで作成・管理 | 1.1.0 |
| [jp-legal-amendment-pdf2md](skills/jp-legal-amendment-pdf2md/) | 法令改正PDF（縦書き・新旧対照表）をMarkdownに変換 | 1.1.0 |
| [mf-hitorihojin-guide](skills/mf-hitorihojin-guide/) | マネーフォワード クラウド ひとり法人プランのガイド | 1.2.0 |
| [yayoi-aoiro-guide](skills/yayoi-aoiro-guide/) | やよいの青色申告オンラインの利用ガイド | 1.0.0 |
| [aml-cft-guide](skills/aml-cft-guide/) | AML/CFT（マネロン・テロ資金対策）の専門知識・試験対策 | 1.0.0 |

### Claude Code ツール

| スキル名 | 説明 | バージョン |
|---------|------|-----------|
| [claude-code-guide](skills/claude-code-guide/) | Claude Codeの機能・設定・ベストプラクティス | 1.1.0 |
| [claude-md-guide](skills/claude-md-guide/) | CLAUDE.mdファイルの作成・最適化ガイド | 2.1.0 |
| [claude-mem-guide](skills/claude-mem-guide/) | claude-memプラグインのセットアップ・トラブルシューティング | - |
| [claude-skill-creation-guide](skills/claude-skill-creation-guide/) | Agent Skillsの作成・管理ガイド | 2.1.0 |
| [claude-insight-reflect](skills/claude-insight-reflect/) | Insightレポート生成・翻訳・CLAUDE.md反映 | - |
| [claude-rename](skills/claude-rename/) | セッションリネーム | - |
| [claude-sessions-sync](skills/claude-sessions-sync/) | 全クライアント間のセッション一覧同期 | - |

### ドキュメント変換

| スキル名 | 説明 | バージョン |
|---------|------|-----------|
| [pdf2md-docling](skills/pdf2md-docling/) | Docling + TableFormerによるPDF→Markdown変換 | 3.20.0 |

### ユーティリティ

| スキル名 | 説明 | バージョン |
|---------|------|-----------|
| [feedly-intelligence-report](skills/feedly-intelligence-report/) | Feedly記事のスコアリング・インテリジェンスレポート生成 | - |
| [happy-mobile-client](skills/happy-mobile-client/) | Happy（Claude Code Mobile Client）セットアップガイド | 2.0.0 |
| [openclaw-guide](skills/openclaw-guide/) | OpenClawセルフホストAIエージェントのセットアップ・セキュリティガイド | - |

## ディレクトリ構成

```
agent-skills/
├── .claude-plugin/
│   └── manifest.json      # Claude Code プラグイン設定
├── skills/
│   ├── aml-cft-guide/
│   ├── claude-code-guide/
│   ├── claude-insight-reflect/
│   ├── claude-md-guide/
│   ├── claude-mem-guide/
│   ├── claude-rename/
│   ├── claude-sessions-sync/
│   ├── claude-skill-creation-guide/
│   ├── feedly-intelligence-report/
│   ├── happy-mobile-client/
│   ├── jp-aoiro-accounting/
│   ├── jp-eltax-guide/
│   ├── jp-etax-guide/
│   ├── jp-law-verification/
│   ├── jp-legal-amendment-pdf2md/
│   ├── mf-hitorihojin-guide/
│   ├── openclaw-guide/
│   ├── pdf2md-docling/
│   └── yayoi-aoiro-guide/
├── CONTRIBUTING.md        # 貢献ガイドライン
├── LICENSE
└── README.md
```

## 貢献

貢献を歓迎します！詳細は [CONTRIBUTING.md](CONTRIBUTING.md) をご覧ください。

## ライセンス

Apache License 2.0 - 詳細は [LICENSE](LICENSE) を参照してください。

## 関連リンク

- [Agent Skills 仕様](https://agentskills.io/)
- [Claude Code ドキュメント](https://code.claude.com/docs)
- [Anthropic Skills リポジトリ](https://github.com/anthropics/skills)
