---
name: happy-mobile-client
description: Happy - Claude Code Mobile Clientのセットアップ、稼働状況確認、トラブルシューティングを支援。スマホからClaude Codeを操作する際の環境構築、QRコードペアリング、セッション管理、エラー対処方法を提供。Happyやモバイルクライアント、スマホからのClaude Code操作に関する質問時に使用。
version: 2.0.0
author: claude_code
createDate: 2026-01-15
updateDate: 2026-02-11
license: Apache-2.0
disable-model-invocation: true
---

# Happy - Claude Code Mobile Client

HappyはClaude Codeをスマホ（iOS/Android）から操作できる無料のオープンソースクライアント。E2E暗号化、音声会話（STT/TTS）、プッシュ通知対応。

## セットアップ

### 1. 前提条件

```bash
node --version && npm --version && claude --version
```

### 2. インストール

```bash
# CLI
npm install -g happy-coder

# モバイルアプリ
# iOS: App Store「Happy: Codex & Claude Code App」
# Android: Google Play「Happy」
```

### 3. ペアリング

```bash
cd /path/to/project
happy  # QRコード表示→スマホでスキャン
```

## 基本コマンド

```bash
happy                                    # デフォルト起動（sonnet）
happy -m opus                            # モデル指定
happy --permission-mode acceptEdits      # 編集自動承認
happy --yolo                             # 全権限スキップ（--dangerously-skip-permissionsのショートカット）
happy --resume                           # 前回セッションを再開
happy codex                              # Codex経由
happy gemini                             # Gemini経由（ACP）
happy daemon                             # バックグラウンドサービス（スマホから新セッション起動可能）
happy doctor                             # システム診断
```

**注意**: `-p` は Claude Code の `--print`（非対話モード）のショートカットであり、パーミッション設定ではない。パーミッションは `--permission-mode` を使用すること。

### パーミッションモード

| モード | 説明 |
|--------|------|
| `default` | 都度確認（デフォルト） |
| `acceptEdits` | ファイル編集を自動承認 |
| `plan` | コード変更前にプラン確認 |
| `bypassPermissions` | すべて自動承認（`--yolo` と同等） |

複数セッション並列実行可能（各セッションは独立したコンテキスト保持）。

## 音声機能（Voice Agent）

Happyの音声機能は単純なディクテーションではなく、**Voice Agent**による双方向の音声会話。

### アーキテクチャ

```
スマホ(マイク) → [Eleven Labs STT] → Voice Agent(Claude Sonnet 4) → Claude Code
スマホ(スピーカー) ← [Eleven Labs TTS] ← Voice Agent(Claude Sonnet 4) ←┘
```

- **STT（音声→テキスト）**: Eleven Labs による音声認識
- **TTS（テキスト→音声）**: Eleven Labs による音声読み上げ
- **Voice Agent**: Claude Sonnet 4 が中間レイヤーとして動作し、発話を整理・構造化してClaude Codeに送信
- Voice Agentは**Claude Codeセッションとは独立したコンテキスト**を保持

### 音声設定（アプリ内）

- **言語**: 日本語/英語の切り替え
- **入力モード**: 連続/プッシュトーク
- **ノイズキャンセリング**: ON/OFF

### 注意事項

- STT/TTSはEleven Labs経由のため**インターネット接続が必要**（完全ローカルではない）
- Claude Codeの生コード出力を読み上げるのではなく、Voice Agentが会話的に応答を返す
- ブレスト・ラバーダックデバッグ・指示出しに適している

## 稼働状況確認

```bash
# 自動チェックスクリプト
bash .claude/skills/happy-mobile-client/scripts/check_happy_status.sh

# 手動確認
ps aux | grep happy           # プロセス
lsof -i -P | grep happy       # ポート

# システム診断
happy doctor
```

## トラブルシューティング

### QRコード表示されない

```bash
claude auth login                           # 再認証
npm uninstall -g happy-coder && \
npm install -g happy-coder                  # 再インストール
```

### 接続エラー

```bash
ping google.com                             # ネットワーク確認
# macOS: システム設定 > ネットワーク > ファイアウォール
```

### モバイル接続不可

1. Happyを再起動してQRコード再表示
2. スマホアプリを再起動
3. ネットワーク接続を確認
4. アプリを再インストール

### 音声が機能しない

1. マイク権限を確認（iOS: 設定 > Happy > マイク、Android: 設定 > アプリ > Happy > 権限 > マイク）
2. インターネット接続を確認（Eleven Labs STT/TTSはオンライン必須）
3. アプリ内で言語設定を確認

**詳細**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)参照

## 主要機能

- **音声会話（Voice Agent）**: Eleven Labs STT/TTS + Claude Sonnet 4による双方向音声対話
- **プッシュ通知**: 権限リクエスト、タスク完了、エラー時
- **会話履歴同期**: オフラインでもアクセス可能
- **E2E暗号化**: TweetNaCl（Signal同等）
- **デーモンモード**: PCから離れてもスマホから新セッション起動可能

## セキュリティ

- 公共Wi-Fi使用時はVPN経由推奨
- QRコードを他人に見せない
- 定期的に再認証（`claude auth login`）

## 追加リソース

- [REFERENCE.md](REFERENCE.md) - 高度な設定、API統合、パフォーマンス最適化
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 詳細なエラー診断・解決策
- [EXAMPLES.md](EXAMPLES.md) - 使用シナリオと実践例

## リンク

- 公式: https://happy.engineering/
- ドキュメント: https://happy.engineering/docs/
- GitHub: https://github.com/slopus/happy
- App Store: https://apps.apple.com/us/app/happy-codex-claude-code-app/id6748571505

## チェックリスト

**セットアップ**:
- [ ] Node.js/npm/Claude Codeインストール済み
- [ ] happy-coderインストール済み
- [ ] モバイルアプリインストール済み
- [ ] QRコードでペアリング完了

**トラブル時**:
- [ ] `happy doctor` で診断実行
- [ ] Happyプロセス実行中
- [ ] ネットワーク接続正常
- [ ] ファイアウォール未ブロック
- [ ] Claude Code認証有効

---

**Version**: 2.0.0 | **Updated**: 2026-02-11
