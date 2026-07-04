# Happy Mobile Client Skill

Happy - Claude Code Mobile Clientのセットアップ、稼働状況確認、トラブルシューティングを支援するClaude Code Agent Skillです。

## 概要

このスキルは、スマホ（iOS/Android）からClaude Codeを操作する際の以下をサポートします：

- 環境構築とセットアップ
- QRコードペアリング
- セッション管理
- エラー対処方法
- パフォーマンス最適化

## ファイル構成

```
happy-mobile-client/
├── SKILL.md                      # メイン指示（318行）
├── REFERENCE.md                  # 詳細リファレンス
├── TROUBLESHOOTING.md            # トラブルシューティングガイド
├── README.md                     # このファイル
└── scripts/
    └── check_happy_status.sh     # 稼働状況チェックスクリプト
```

## 使用方法

### スキルの起動

このスキルは以下のキーワードで自動的にトリガーされます：

- Happy
- モバイルクライアント
- スマホからClaude Code操作
- happy-coder
- QRコードペアリング

### 手動での起動

```bash
# Claude Code内で実行
/skill happy-mobile-client
```

### 稼働状況チェック

```bash
# ステータスチェックスクリプトを実行
bash .claude/skills/happy-mobile-client/scripts/check_happy_status.sh
```

## 主要機能

### 1. セットアップ支援

- Node.js/npmの確認
- happy-coderのインストール
- モバイルアプリのダウンロード
- QRコードペアリング

### 2. 稼働状況確認

自動チェック項目：
- Node.js & npm
- happy-coderインストール状態
- Claude Code認証状態
- 実行中のプロセス
- ネットワーク接続
- ポート使用状況
- システムリソース

### 3. トラブルシューティング

以下の問題に対する解決策を提供：
- インストール関連
- 接続の問題
- 認証エラー
- パフォーマンス問題
- モバイルアプリの問題

## ドキュメント

### SKILL.md
- セットアップ手順（前提条件、インストール、ペアリング）
- 基本的な使い方（起動コマンド、セッション管理）
- 稼働状況確認方法
- トラブルシューティング（よくある問題と解決策）
- 主要機能の説明
- チェックリスト

### REFERENCE.md
- アーキテクチャ（システム構成、データフロー、暗号化）
- 高度な設定（環境変数、プロキシ、カスタム設定）
- API統合（Webhook、カスタムスクリプト）
- セキュリティ詳細（認証、鍵管理、監査ログ）
- パフォーマンス最適化
- CI/CD統合

### TROUBLESHOOTING.md
- インストール関連の問題
- 接続の問題（QRコード表示、モバイル接続、切断）
- 認証の問題（Claude Code認証、セッショントークン、鍵の不整合）
- パフォーマンスの問題（応答遅延、メモリ、CPU）
- モバイルアプリの問題（クラッシュ、音声入力、通知）
- エラーメッセージ詳細

## スクリプト

### check_happy_status.sh

Happy Mobile Clientの包括的な稼働状況チェックを実行します。

**チェック項目**：
1. Node.js & npm
2. happy-coderインストール
3. Claude Code認証
4. 実行中のプロセス
5. ネットワーク接続
6. ポート使用状況
7. システムリソース

**使用例**：
```bash
bash .claude/skills/happy-mobile-client/scripts/check_happy_status.sh
```

**出力例**：
```
=========================================
Happy Mobile Client - Status Check
=========================================

1. Node.js & npm
-------------------
✓ Node.js installed: v18.0.0
✓ npm installed: 9.0.0

2. happy-coder Installation
-------------------
✓ happy-coder installed: 1.5.0

...

=========================================
Summary
=========================================
✓ All required components are ready
```

## Progressive Disclosure

このスキルは[Progressive Disclosure原則](../claude-skill-creation-guide/PROGRESSIVE-DISCLOSURE.md)に従って設計されています：

| Level | 内容 | トークンコスト |
|-------|------|----------------|
| Level 1 | YAMLフロントマター（name, description） | ~100トークン |
| Level 2 | SKILL.md本文（セットアップ、使い方、トラブルシューティング） | ~3,000トークン |
| Level 3+ | REFERENCE.md, TROUBLESHOOTING.md, scripts | 必要時のみ |

## 設計原則

### 簡潔さ
- SKILL.mdは318行（500行未満の要件を満たす）
- 詳細情報は別ファイルに分離
- Claudeが既に知っている情報は省略

### 実行可能性
- ステータスチェックスクリプトを提供
- エラー処理を含む
- 診断結果を明確に表示

### 段階的開示
- 基本情報をSKILL.mdに
- 高度な設定をREFERENCE.mdに
- 詳細なトラブルシューティングを専用ファイルに

## 対応プラットフォーム

- **macOS**: フルサポート（ステータスチェックスクリプト含む）
- **Linux**: 基本サポート（一部スクリプト要調整）
- **Windows**: 基本サポート（bashスクリプトは要WSL）

## 必要な環境

- Node.js 18以上
- npm 9以上
- Claude Code CLI 2.0以上
- macOS 12以上 / iOS 15.1以上 / Android 8以上

## ベストプラクティス

1. **定期的なステータスチェック**: 問題発生前にスクリプトを実行
2. **ログの確認**: トラブル時は `~/.happy/logs/happy.log` を参照
3. **アップデート**: happy-coderとモバイルアプリを最新に保つ
4. **セキュリティ**: 公共Wi-Fi使用時はVPN経由で接続

## トラブルシューティング

問題が発生した場合：

1. **ステータスチェックを実行**
   ```bash
   bash .claude/skills/happy-mobile-client/scripts/check_happy_status.sh
   ```

2. **TROUBLESHOOTING.mdを参照**
   - 具体的な症状から解決策を検索

3. **ログを確認**
   ```bash
   tail -f ~/.happy/logs/happy.log
   ```

4. **コミュニティに質問**
   - GitHub Issues
   - 公式フォーラム

## 関連リソース

- **公式サイト**: https://happy.engineering/
- **GitHub**: https://github.com/slopus/happy
- **App Store**: https://apps.apple.com/us/app/happy-codex-claude-code-app/id6748571505
- **ドキュメント**: https://happy.engineering/docs/features/

## ライセンス

このスキルはMITライセンスの下で公開されています。

## バージョン履歴

- **v1.0.0** (2026-01-15): 初版作成
  - セットアップ手順
  - 稼働状況チェックスクリプト
  - 包括的なトラブルシューティングガイド
  - 詳細リファレンス

## 作者

Claude Code

## フィードバック

改善提案やバグレポートは、プロジェクトのIssue trackerまでお願いします。

---

**Last Updated**: 2026-01-15
**Version**: 1.0.0
