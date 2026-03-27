# claude-mem-guide

Claude Codeの永続メモリプラグイン「claude-mem」のセットアップ・トラブルシューティングガイド。

## 概要

このスキルは、[claude-mem](https://github.com/thedotmack/claude-mem)プラグインの導入・設定・問題解決を支援します。

## 対象ユーザー

- claude-memプラグインを新規インストールする方
- VSCode/Cursor環境でclaude-memが動作しない方
- hookの設定方法を知りたい方

## 主な内容

- インストール手順（Bun、プラグイン、PATH設定）
- VSCode/Cursor環境でのhooks手動設定
- 動作確認方法（ワーカー、統計、ログ）
- MCPツールの3層検索ワークフロー
- トラブルシューティング

## 使用方法

Claude Codeで以下のように呼び出します：

```
/claude-mem-guide
```

または、claude-mem関連の質問をすると自動的に呼び出されます：
- 「claude-memが動作しない」
- 「メモリが記録されない」
- 「hookの設定方法」

## 関連リソース

- [claude-mem GitHub](https://github.com/thedotmack/claude-mem)
- [Claude Code Hooks Guide](https://docs.anthropic.com/claude-code/hooks)

## ライセンス

MIT
