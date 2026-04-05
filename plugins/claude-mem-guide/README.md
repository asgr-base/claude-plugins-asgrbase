# claude-mem-guide

Claude Codeの永続メモリプラグイン「claude-mem」のセットアップ・トラブルシューティングガイド。

## 概要

このスキルは、[claude-mem](https://github.com/thedotmack/claude-mem)プラグインの導入・設定・問題解決を支援します。

## 対象ユーザー

- claude-memプラグインを新規インストールする方
- ワーカー起動やMCPサーバーの問題を解決したい方
- hookの設定方法を知りたい方

## 主な内容

- インストール手順（Bun、Node.js、プラグイン、PATH設定）
- LLMプロバイダー設定（claude推奨、Gemini/OpenRouterの注意点）
- ワーカー管理（起動・停止・Stale PIDファイル対処）
- 動作確認方法（ワーカー、mcpReady、統計、ログ）
- MCPツールの3層検索ワークフロー
- トラブルシューティング（20+パターン）

## 使用方法

Claude Codeで以下のように呼び出します：

```
/claude-mem-guide
```

または、claude-mem関連の質問をすると自動的に呼び出されます：
- 「claude-memをセットアップして」
- 「claude-memが動作しない」
- 「メモリが記録されない」
- 「ワーカーが起動しない」

## 関連リソース

- [claude-mem GitHub](https://github.com/thedotmack/claude-mem)
- [Claude Code Hooks Guide](https://docs.anthropic.com/claude-code/hooks)

## ライセンス

Apache-2.0
