# Happy Mobile Client - 使用例

実際の使用シナリオとベストプラクティスを紹介します。

## 目次

- [基本的な使用例](#基本的な使用例)
- [実践シナリオ](#実践シナリオ)
- [高度な使用例](#高度な使用例)
- [チーム利用](#チーム利用)

## 基本的な使用例

### 1. 初回セットアップから利用開始まで

```bash
# Step 1: インストール
npm install -g happy-coder

# Step 2: プロジェクトディレクトリに移動
cd ~/projects/myapp

# Step 3: Happyを起動
happy

# Step 4: スマホアプリでQRコードをスキャン
# → ペアリング完了

# Step 5: スマホからClaude Codeを操作
# 「このプロジェクトの構造を教えて」と入力
```

### 2. モデルを指定して起動

```bash
# Opusモデルで複雑なタスク
happy -m opus

# Haikuモデルで簡単なタスク（高速・低コスト）
happy -m haiku

# Sonnetモデル（バランス型、デフォルト）
happy -m sonnet
```

### 3. パーミッションモードの使い分け

```bash
# 編集自動承認モード（信頼できる操作のみ）
happy --permission-mode acceptEdits

# デフォルトモード（都度確認）
happy --permission-mode default

# プランモード（実行前に計画確認）
happy --permission-mode plan

# 全権限スキップ（--dangerously-skip-permissions のショートカット）
happy --yolo
```

**注意**: `-p` は Claude Code の `--print`（非対話モード）のショートカットであり、パーミッション設定ではない。

## 実践シナリオ

### シナリオ1: 外出先からのコードレビュー

**状況**: 通勤電車の中でプルリクエストのレビューを実施

**Mac側（自宅または会社）**:
```bash
cd ~/projects/myapp
git checkout feature/new-login-flow
happy --permission-mode default
```

**スマホ側**:
```
音声入力: 「現在のブランチの変更をレビューして」

Claude Codeの応答:
- 変更ファイル一覧を表示
- コードの品質分析
- セキュリティチェック
- 改善提案

音声入力: 「auth.tsのログイン処理にコメントを追加して」
→ Mac側でファイルが自動編集される
```

**メリット**:
- 移動時間を有効活用
- 音声入力で両手フリー
- プッシュ通知で完了を即座に確認

### シナリオ2: リモートでのバグ修正

**状況**: 本番環境でバグ発見、外出先から緊急対応

**Mac側（常時起動）**:
```bash
cd ~/projects/production-app
happy -m opus --permission-mode plan
```

**スマホ側**:
```
1. プッシュ通知: 「バグレポート受信」

2. 入力: 「エラーログを確認して」
   → Claude Codeがログファイルを解析

3. 入力: 「原因を特定して修正案を提示して」
   → 原因と3つの修正案を表示

4. 入力: 「修正案2を実装して」
   → プランモードで実行計画を表示
   → 承認後、自動実装

5. 入力: 「テストを実行して」
   → プッシュ通知: 「テスト成功」

6. 入力: 「コミットしてプルリクエストを作成」
   → プッシュ通知: 「PR作成完了」
```

**メリット**:
- 迅速な対応
- 実装前に計画確認（プランモード）
- 完了をプッシュ通知で確認

### シナリオ3: 複数プロジェクトの並行管理

**状況**: フロントエンドとバックエンドを同時開発

**Mac側（複数ターミナル）**:
```bash
# ターミナル1: フロントエンド
cd ~/projects/frontend
happy -m sonnet

# ターミナル2: バックエンド
cd ~/projects/backend
happy -m opus

# ターミナル3: インフラ
cd ~/projects/infrastructure
happy -m haiku
```

**スマホ側**:
```
Happyアプリでセッション一覧:
[1] frontend (sonnet)
[2] backend (opus)
[3] infrastructure (haiku)

操作:
1. [1]を選択: 「Reactコンポーネントを作成」
2. [2]を選択: 「APIエンドポイントを追加」
3. [3]を選択: 「デプロイスクリプトを確認」

各セッションは独立してコンテキストを保持
```

**メリット**:
- 複数プロジェクトをシームレスに切り替え
- 各セッションの履歴が独立
- モデルを用途別に最適化

### シナリオ4: 音声コーディング（ハンズフリー開発）

**状況**: 子供を抱っこしながらコーディング

**セットアップ**:
```bash
cd ~/projects/myapp
happy -m sonnet --yolo
```

**スマホ側（音声のみ）**:
```
🎤 「新しいファイルを作成、パス: src/utils/validation.ts」
→ ファイル作成完了

🎤 「メールアドレスをバリデートする関数を書いて」
→ 関数実装

🎤 「テストも書いて」
→ テストファイル作成・実装

🎤 「リントエラーを修正して」
→ 自動修正

🎤 「コミット」
→ プッシュ通知: 「コミット完了」
```

**メリット**:
- 完全ハンズフリー
- 自動承認モードで中断なし
- プッシュ通知で進捗確認

## 高度な使用例

### 環境変数を使用した起動

```bash
# 特定のAPI keyを設定
happy --claude-env API_KEY=your_api_key

# 複数の環境変数
happy --claude-env DB_HOST=localhost \
      --claude-env DB_PORT=5432 \
      --claude-env ENV=development
```

### カスタム引数の指定

```bash
# デバッグモード
happy --claude-arg --verbose --claude-arg --debug

# ログファイル指定
happy --claude-arg --log-file=/tmp/claude.log
```

### Codex経由での起動

```bash
# Codexを使用（異なるワークフロー）
happy codex

# Codexにモデルを指定
happy codex -m opus
```

### VPN経由での安全な接続

```bash
# Step 1: VPNに接続
# macOS: ネットワーク設定からVPN接続

# Step 2: Happyを起動
happy

# Step 3: スマホもVPN接続
# iOS/Android: VPNアプリで同じVPNに接続

# Step 4: ペアリング
# → 暗号化通信がVPN経由でさらに安全に
```

## チーム利用

### ペアプログラミング

**シチュエーション**: リモートペアプログラミング

```bash
# ドライバー（Mac側）
cd ~/projects/pair-session
happy --permission-mode plan

# ナビゲーター（スマホ側）
# 画面を見ながら指示を出す
「エッジケースのテストを追加して」
「変数名をより明確にして」
「エラーハンドリングを強化して」
```

### コードレビューワークフロー

```bash
# レビュアー（Mac側）
cd ~/projects/review
git checkout pr/123
happy

# スマホ側
「PRの変更を要約して」
「セキュリティ上の問題をチェック」
「パフォーマンスへの影響を分析」
「レビューコメントをMarkdownで生成」
```

### ナレッジ共有

```bash
# メンター（Mac側）
cd ~/projects/learning
happy

# スマホ側（学習者）
「このコードベースのアーキテクチャを説明して」
「認証フローを図で表示して」
「ベストプラクティスを教えて」
```

## ベストプラクティス

### 1. セッション管理

```bash
# セッション名をわかりやすく（プロジェクト名をディレクトリで識別）
cd ~/projects/frontend-app    # セッション: frontend-app
cd ~/projects/backend-api     # セッション: backend-api

# 不要なセッションは終了（Ctrl+C）
```

### 2. モデル選択の指針

```bash
# 簡単なタスク: Haiku（高速・低コスト）
happy -m haiku  # ファイル一覧、簡単な質問

# 通常のタスク: Sonnet（バランス）
happy -m sonnet  # 実装、リファクタリング

# 複雑なタスク: Opus（高性能）
happy -m opus  # アーキテクチャ設計、複雑なバグ修正
```

### 3. パーミッションモードの使い分け

```bash
# 編集のみ自動承認（おすすめ）
happy --permission-mode acceptEdits  # ファイル編集は自動、他は確認

# 慎重な操作: plan
happy --permission-mode plan         # DB変更、デプロイ、重大な変更

# 全自動（信頼できる環境のみ）
happy --yolo                         # すべて自動承認
```

### 4. セキュリティ

```bash
# 公共Wi-Fi使用時は必ずVPN
# QRコードは他人に見せない
# 定期的な再認証
claude auth login

# セッション終了時はプロセスを停止
# Ctrl+C または pkill happy
```

## トラブルシューティング例

### 例1: 接続が頻繁に切れる

```bash
# 原因: 不安定なネットワーク
# 解決策:

# 1. ネットワーク品質を確認
ping -c 10 8.8.8.8

# 2. タイムアウトを延長
export HAPPY_TIMEOUT=120000  # 2分

# 3. Keep-Aliveを有効化
happy --keep-alive
```

### 例2: メモリ使用量が多い

```bash
# 原因: 長時間のセッション、大量の履歴
# 解決策:

# 1. メモリ最適化モード
happy --optimize-memory

# 2. 履歴を制限
happy --max-history 100

# 3. 定期的にキャッシュクリア
rm -rf ~/.happy/cache/*
```

### 例3: 音声入力が認識されない

```
原因: マイク権限、言語設定、ネットワーク

解決策:
1. iOS: 設定 > Happy > マイク > 許可
2. Android: 設定 > アプリ > Happy > 権限 > マイク
3. アプリ内: 設定 > 言語 > 日本語/英語を選択
4. ネットワーク接続を確認（音声認識はオンライン処理）
```

## まとめ

Happyを使うことで：

- **場所を選ばない開発**: カフェ、電車、自宅どこからでも
- **時間の有効活用**: 移動時間、待ち時間を開発時間に
- **柔軟なワークスタイル**: 音声、テキスト、両手フリー
- **チームコラボレーション**: リモートペアプロ、コードレビュー

さらなる詳細:
- [SKILL.md](SKILL.md) - 基本的な使い方
- [REFERENCE.md](REFERENCE.md) - 高度な設定
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 問題解決

---

**Last Updated**: 2026-02-11
