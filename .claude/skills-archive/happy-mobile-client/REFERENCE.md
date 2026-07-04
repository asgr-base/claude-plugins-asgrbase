# Happy Mobile Client - 詳細リファレンス

## 目次

- [アーキテクチャ](#アーキテクチャ)
- [コマンドラインオプション](#コマンドラインオプション)
- [更新とメンテナンス](#更新とメンテナンス)
- [高度な設定](#高度な設定)
- [API統合](#api統合)
- [カスタマイズ](#カスタマイズ)
- [セキュリティ詳細](#セキュリティ詳細)
- [パフォーマンス最適化](#パフォーマンス最適化)

## アーキテクチャ

### システム構成

```
┌─────────────────┐         ┌──────────────┐
│   macOS (PC)    │         │  Smartphone  │
│                 │         │              │
│  ┌───────────┐  │         │ ┌──────────┐ │
│  │   Happy   │  │ Encrypt │ │  Happy   │ │
│  │    CLI    │◄─┼─────────┼─►   App    │ │
│  └─────┬─────┘  │         │ └──────────┘ │
│        │        │         │              │
│  ┌─────▼─────┐  │         └──────────────┘
│  │  Claude   │  │
│  │   Code    │  │
│  └───────────┘  │
└─────────────────┘
         │
         ▼
    ┌────────────┐
    │ Cloud API  │
    └────────────┘
```

### データフロー

1. **ユーザー入力**: スマホアプリで入力
2. **暗号化**: TweetNaCl (NaCl/libsodium) でE2E暗号化
3. **転送**: Happyサーバー経由でMacのCLIに送信
4. **実行**: Claude Code CLIがタスク実行
5. **応答**: 同じ経路で暗号化されてスマホに返信

### 暗号化の仕組み

Happyは**TweetNaCl**を使用したエンドツーエンド暗号化を実装：

- **鍵交換**: 初回ペアリング時にQRコードで共有
- **対称暗号**: secretbox方式（XSalsa20-Poly1305）
- **認証**: Poly1305 MAC
- **ノンス**: ランダム生成で再利用防止

```javascript
// 暗号化の概念（実際のコードは内部実装）
const encrypted = nacl.secretbox(message, nonce, sharedKey);
const decrypted = nacl.secretbox.open(encrypted, nonce, sharedKey);
```

## コマンドラインオプション

### 基本オプション

```bash
# モデル選択
happy -m, --model <model>      # sonnet, opus, haiku

# パーミッションモード（注意: -p は --print のショートカット。パーミッションには使えない）
happy --permission-mode <mode>  # default, acceptEdits, plan, bypassPermissions, delegate, dontAsk

# 全権限スキップ（--dangerously-skip-permissions のショートカット）
happy --yolo

# 前回セッションの再開
happy --resume

# バージョン確認
happy --version

# ヘルプ表示
happy --help

# システム診断
happy doctor
```

**パーミッションモード一覧**:

| モード | 説明 |
|--------|------|
| `default` | 都度確認（デフォルト） |
| `acceptEdits` | ファイル編集を自動承認 |
| `plan` | コード変更前にプラン確認 |
| `bypassPermissions` | すべて自動承認（`--yolo` と同等） |
| `delegate` | 委譲モード |
| `dontAsk` | 確認なし |

### 環境変数設定

```bash
# Claude Code用の環境変数
happy --claude-env KEY=VALUE

# 複数の環境変数
happy --claude-env VAR1=value1 --claude-env VAR2=value2

# 使用例
happy --claude-env API_KEY=sk-xxx \
      --claude-env DB_HOST=localhost \
      --claude-env ENV=development
```

### 追加引数

```bash
# Claude CLIに引数を渡す
happy --claude-arg <arg>

# 使用例
happy --claude-arg --verbose
happy --claude-arg --debug
happy --claude-arg --log-file=/tmp/claude.log
```

### Codex統合

```bash
# Codex経由で起動
happy codex

# Codexにオプションを指定
happy codex -m opus
happy codex --permission-mode plan
```

### Gemini統合（ACP）

```bash
# Gemini経由で起動
happy gemini
```

### デーモンモード

PCから離れていてもスマホから新しいセッションを起動可能：

```bash
# バックグラウンドサービスとして起動
happy daemon
```

## 更新とメンテナンス

### happy-coderの更新

```bash
# 現在のバージョン確認
npm list -g happy-coder
happy --version

# 最新版に更新
npm update -g happy-coder

# 特定バージョンをインストール
npm install -g happy-coder@1.5.0

# アンインストール
npm uninstall -g happy-coder
```

### モバイルアプリの更新

**iOS**:
1. App Storeを開く
2. アカウントアイコンをタップ
3. 下にスクロールして「Happy」を探す
4. 「アップデート」をタップ

または自動更新を有効化：
- 設定 > App Store > Appのアップデート > ON

**Android**:
1. Google Play Storeを開く
2. プロフィールアイコン > アプリとデバイスの管理
3. 「Happy」を探す
4. 「更新」をタップ

または自動更新を有効化：
- Play Store > アプリの詳細 > ⋮ > 自動更新を有効にする

### キャッシュクリア

```bash
# Happyのキャッシュをクリア
rm -rf ~/.happy/cache

# npm キャッシュもクリア（再インストール時）
npm cache clean --force
```

### ログのローテーション

```bash
# ログファイルのサイズを確認
du -h ~/.happy/logs/happy.log

# ログをアーカイブ
mv ~/.happy/logs/happy.log ~/.happy/logs/happy.log.$(date +%Y%m%d)

# 古いログを削除（30日以上前）
find ~/.happy/logs -name "*.log.*" -mtime +30 -delete
```

## 高度な設定

### 設定ファイルの場所

macOS:
```
~/.happy/config.json
~/.config/happy/config.json
```

### カスタム設定例

```json
{
  "server": {
    "url": "https://custom-server.example.com",
    "port": 8080,
    "timeout": 30000
  },
  "encryption": {
    "algorithm": "nacl-secretbox",
    "keyRotationDays": 90
  },
  "notifications": {
    "enabled": true,
    "sound": true,
    "vibration": true
  },
  "logging": {
    "level": "info",
    "file": "~/.happy/logs/happy.log"
  }
}
```

### 環境変数

```bash
# HappyサーバーのカスタムURL
export HAPPY_SERVER_URL="https://your-server.com"

# ログレベル設定
export HAPPY_LOG_LEVEL="debug"

# タイムアウト設定（ミリ秒）
export HAPPY_TIMEOUT=60000

# カスタムポート
export HAPPY_PORT=9000
```

### プロキシ設定

```bash
# HTTPプロキシ経由
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="https://proxy.example.com:8443"

# 認証付きプロキシ
export HTTP_PROXY="http://user:pass@proxy.example.com:8080"
```

## API統合

### Webhookの設定

Happy CLIはwebhookをサポートし、特定のイベントで外部APIを呼び出せます：

```json
{
  "webhooks": {
    "onSessionStart": "https://api.example.com/session/start",
    "onSessionEnd": "https://api.example.com/session/end",
    "onError": "https://api.example.com/error"
  }
}
```

### カスタムスクリプト統合

```bash
# Happy起動前に実行するスクリプト
happy --pre-hook "./scripts/setup.sh"

# Happy終了後に実行するスクリプト
happy --post-hook "./scripts/cleanup.sh"
```

## カスタマイズ

### カスタムコマンド

`.happy/commands.json` でカスタムコマンドを定義：

```json
{
  "commands": {
    "deploy": {
      "description": "Deploy to production",
      "script": "./scripts/deploy.sh",
      "confirm": true
    },
    "test": {
      "description": "Run test suite",
      "script": "npm test"
    }
  }
}
```

使用例:
```bash
happy --command deploy
```

### テンプレート

頻繁に使用するプロンプトをテンプレート化：

`.happy/templates.json`:
```json
{
  "templates": {
    "code-review": "Review the current changes and provide feedback",
    "refactor": "Refactor the selected code for better readability",
    "debug": "Debug the error in {file} at line {line}"
  }
}
```

## セキュリティ詳細

### 認証メカニズム

1. **初回ペアリング**:
   - 秘密鍵ペア生成（Ed25519）
   - QRコードに公開鍵と接続情報を含める
   - スマホアプリでスキャン後、鍵交換完了

2. **セッション認証**:
   - 各セッションで一意のセッショントークン生成
   - トークンの有効期限: 24時間（デフォルト）

### 鍵の保存場所

```
~/.happy/
├── private_key.enc    # 暗号化された秘密鍵
├── public_key.pem     # 公開鍵
└── session_tokens.db  # セッショントークン
```

### セキュリティベストプラクティス

1. **定期的な鍵ローテーション**:
```bash
# 鍵を再生成（既存セッションは無効化）
happy --regenerate-keys
```

2. **セッション管理**:
```bash
# アクティブセッションの確認
happy --list-sessions

# 特定セッションの無効化
happy --revoke-session <session-id>

# 全セッションの無効化
happy --revoke-all
```

3. **監査ログ**:
```bash
# 監査ログの有効化
export HAPPY_AUDIT_LOG=~/.happy/audit.log

# ログの確認
tail -f ~/.happy/audit.log
```

## パフォーマンス最適化

### メモリ管理

```bash
# Node.jsのヒープサイズを増やす
export NODE_OPTIONS="--max-old-space-size=4096"

# V8の最適化フラグ
export NODE_OPTIONS="--optimize-for-size"
```

### 接続プーリング

複数セッションを効率的に管理：

```json
{
  "performance": {
    "connectionPoolSize": 5,
    "keepAliveTimeout": 5000,
    "maxConcurrentSessions": 3
  }
}
```

### キャッシュ設定

```json
{
  "cache": {
    "enabled": true,
    "ttl": 3600,
    "maxSize": "100MB",
    "strategy": "lru"
  }
}
```

### ネットワーク最適化

```bash
# 圧縮を有効化
happy --enable-compression

# バッチリクエスト
happy --batch-requests

# リクエストタイムアウトの調整
happy --request-timeout 30000
```

## ログとデバッグ

### ログレベル

```bash
# デバッグモード
happy --log-level debug

# 詳細ログ
happy --verbose

# サイレントモード（エラーのみ）
happy --quiet
```

### ログ出力先

```bash
# ファイルに出力
happy --log-file ~/.happy/happy.log

# syslogに送信（macOS/Linux）
happy --log-syslog

# 標準出力とファイル両方
happy --log-file ~/.happy/happy.log --log-stdout
```

### トレースモード

```bash
# 完全なトレース（パフォーマンス分析用）
happy --trace

# ネットワークトレース
happy --trace-network

# API呼び出しトレース
happy --trace-api
```

## モバイルアプリの高度な機能

### オフラインモード

- 会話履歴はローカルキャッシュに保存
- オフライン時は送信キューに追加
- オンライン復帰時に自動送信

### 音声機能（Voice Agent）

Happyの音声機能は単純なSTTではなく、**Voice Agent**による双方向の音声会話システム。

#### アーキテクチャ

```
スマホ(マイク) → [Eleven Labs STT] → Voice Agent(Claude Sonnet 4) → Claude Code
スマホ(スピーカー) ← [Eleven Labs TTS] ← Voice Agent(Claude Sonnet 4) ←┘
```

#### コンポーネント

| コンポーネント | 技術 | 役割 |
|---------------|------|------|
| **STT** | Eleven Labs | 音声→テキスト変換 |
| **TTS** | Eleven Labs | テキスト→音声読み上げ |
| **Voice Agent** | Claude Sonnet 4 | 発話の整理・構造化、Claude Codeへのプロンプト変換 |

#### Voice Agentの特性

- Claude Codeセッションとは**独立したコンテキスト**を保持
- ユーザーの「あのー」「えっと」等のフィラーワードを除去し、構造化されたプロンプトに変換
- コーディングのアイデアをブレストし、実行に移す前に反復する用途に最適
- Claude Codeの生コード出力を読み上げるのではなく、**会話的に応答を返す**

#### 音声設定（アプリ内）

- **言語**: 日本語/英語の切り替え
- **音声入力モード**: 連続/プッシュトーク
- **ノイズキャンセリング**: ON/OFF

#### 制約事項

- STT/TTSはEleven Labs経由のため**インターネット接続が必須**
- 完全ローカル処理は不可（ローカルSTT/TTSが必要な場合はVoiceMode MCPを検討）

### プッシュ通知のカスタマイズ

アプリ設定で通知タイプを個別に制御：

- タスク完了通知
- エラー通知
- 権限リクエスト通知
- セッション状態変更通知

## バックアップとリストア

### 設定のバックアップ

```bash
# 設定をエクスポート
happy --export-config > ~/.happy/backup/config-$(date +%Y%m%d).json

# 会話履歴をエクスポート
happy --export-history > ~/.happy/backup/history-$(date +%Y%m%d).json
```

### リストア

```bash
# 設定を復元
happy --import-config ~/.happy/backup/config-20260115.json

# 会話履歴を復元
happy --import-history ~/.happy/backup/history-20260115.json
```

## CI/CD統合

### GitHub Actions

```yaml
name: Happy CI
on: [push]
jobs:
  happy-check:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install Happy
        run: npm install -g happy-coder
      - name: Run Happy Check
        run: happy --check
        env:
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
```

### ヘッドレスモード

CI環境でHappyを使用：

```bash
# QRコード表示なしで起動（API経由で認証）
happy --headless --api-key $CLAUDE_API_KEY
```

## コミュニティと拡張

### プラグインシステム

Happyは拡張可能：

```javascript
// ~/.happy/plugins/custom-plugin.js
module.exports = {
  name: 'custom-plugin',
  version: '1.0.0',
  hooks: {
    beforeCommand: (command) => {
      console.log(`Executing: ${command}`);
    },
    afterResponse: (response) => {
      console.log(`Response: ${response}`);
    }
  }
};
```

プラグインの有効化:
```bash
happy --plugin ~/.happy/plugins/custom-plugin.js
```

## リソース

- **公式ドキュメント**: https://happy.engineering/docs/
- **GitHub Issues**: https://github.com/slopus/happy/issues
- **Discord コミュニティ**: [リンクは公式サイトで確認]
- **Stack Overflow**: タグ `happy-coder`

---

**Last Updated**: 2026-02-11
