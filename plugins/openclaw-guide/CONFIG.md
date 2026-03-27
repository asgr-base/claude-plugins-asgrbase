# OpenClaw 設定リファレンス

## 設定ファイルの場所

```
~/.openclaw/openclaw.json    # メイン設定
~/.openclaw/nodes/           # ペアリング済みノードのトークン情報
~/.openclaw/agents/          # エージェント設定・セッション情報
```

## 設定例（最小構成）

```json
{
  "gateway": {
    "port": 18789,
    "bind": "loopback",
    "mode": "local",
    "auth": {
      "mode": "token",
      "token": "<your-token>"
    }
  }
}
```

## Tailscale Serve 連携時の設定例

```json
{
  "gateway": {
    "port": 18789,
    "bind": "loopback",
    "mode": "local",
    "auth": {
      "mode": "token",
      "token": "<your-token>"
    },
    "tailscale": {
      "mode": "serve",
      "resetOnExit": false
    }
  }
}
```

`resetOnExit: false` にすることで、Gateway 停止後も Tailscale Serve 設定が維持される。

## 設定の確認・変更

```bash
# 設定全体を確認
cat ~/.openclaw/openclaw.json | jq .

# 特定の設定値を確認
openclaw config get gateway.auth.mode
openclaw config get gateway.port

# 設定値を変更
openclaw config set gateway.auth.token <new_token>
```

## 重要な設定キーの説明

### gateway.bind

| 値 | 意味 |
|----|------|
| `"loopback"` | 127.0.0.1のみ（推奨・セキュア） |
| `"local"` | ローカルネットワーク全体 |
| `"public"` | インターネット公開（危険） |

**推奨構成**: `loopback` + `tailscale.mode: "serve"` の組み合わせで、Tailscale Serve 経由でのみ tailnet 内に公開する。

### gateway.controlUi.allowInsecureAuth

HTTP 経由のトークン認証でデバイスペアリングをスキップする設定。

```json
"controlUi": {
  "allowInsecureAuth": true
}
```

**注意**: Tailscale Serve 経由のリバースプロキシ構成では、この設定だけでは不十分な場合がある。`gateway.trustedProxies` も必要になることがある（Issue #1679）。

### gateway.trustedProxies

リバースプロキシのIPを信頼済みとして設定。`allowInsecureAuth` と組み合わせて使用。

```json
"gateway": {
  "trustedProxies": ["127.0.0.1", "::1", "127.0.0.0/8"]
}
```

## LaunchAgent 設定

```bash
# LaunchAgent plist の場所を確認
ls ~/Library/LaunchAgents/ | grep openclaw

# LaunchAgent 操作
PLIST=$(ls ~/Library/LaunchAgents/ | grep openclaw | head -1)
launchctl load   ~/Library/LaunchAgents/$PLIST    # 起動
launchctl unload ~/Library/LaunchAgents/$PLIST    # 停止
launchctl list | grep openclaw                     # 状態確認

# ログファイルの場所（plist 内で指定）
cat ~/Library/LaunchAgents/$PLIST
```

## セッション・ノード情報の場所

```bash
# セッション履歴
~/.openclaw/agents/<agent-name>/sessions/sessions.json

# ペアリング済みデバイス情報
~/.openclaw/nodes/

# ログファイル
/tmp/openclaw/openclaw-YYYY-MM-DD.log
```

## CLI コマンドリファレンス

```bash
# Gateway 管理
openclaw gateway start      # Gateway を起動
openclaw gateway stop       # Gateway を停止
openclaw gateway status     # 状態確認

# デバイス管理
openclaw devices list                  # デバイス一覧（Pending 含む）
openclaw devices approve <RequestID>   # デバイスを承認
openclaw devices reject <RequestID>    # デバイスを拒否

# 設定管理
openclaw config get <key>              # 設定値を取得
openclaw config set <key> <value>      # 設定値を変更

# 診断・修復
openclaw doctor          # 設定をチェック
openclaw doctor --fix    # 無効な設定キーを自動除去して修復

# バージョン確認
openclaw --version
```

## インストール情報（Homebrew）

```
インストールパス: /opt/homebrew/lib/node_modules/openclaw
CLI バイナリ:     /opt/homebrew/bin/openclaw
実行方式:         /opt/homebrew/bin/node /opt/homebrew/lib/node_modules/openclaw/dist/index.js
Node.js 要件:     v22 以上
```

SSH セッションで PATH が通らない場合は、フルパスを使用するか `-t` オプションで対話セッションを使う。詳細は [TROUBLESHOOTING.md](TROUBLESHOOTING.md) を参照。
