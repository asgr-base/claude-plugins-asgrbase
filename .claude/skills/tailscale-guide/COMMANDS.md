# Tailscale CLI コマンドリファレンス

## 基本操作

### 状態・情報確認

```bash
# ネットワーク全体の状態（ピア一覧、接続状態）
tailscale status

# 自分のTailscale IPアドレス（複数アドレス含む）
tailscale ip

# 特定のアドレスファミリのみ
tailscale ip -4   # IPv4のみ
tailscale ip -6   # IPv6のみ

# バージョン確認
tailscale version

# 詳細な状態（JSON形式）
tailscale status --json | jq .
```

### 接続管理

```bash
# Tailscaleに接続
tailscale up

# 切断（VPN停止）
tailscale down

# 再認証
tailscale login

# ログアウト
tailscale logout
```

### 疎通確認

```bash
# ピアへのping（Tailscale経由）
tailscale ping <server-hostname>
tailscale ping <tailscale-ip>

# pingオプション
tailscale ping --count 5 <server-hostname>    # 5回ping
tailscale ping --timeout 10s <server-hostname> # タイムアウト指定
```

### ネットワーク診断

```bash
# ネットワーク診断（NAT種別、リレー状況）
tailscale netcheck

# デバッグ情報
tailscale debug derp-map

# バグレポート（ログ収集）
tailscale bugreport
```

---

## Tailscale Serve（tailnet内公開）

Tailscale ServeはTailnet内のデバイスにのみHTTP/HTTPSでサービスを公開する機能。

```bash
# HTTPS公開（ポート443 → ローカルポート転送）
tailscale serve https / http://127.0.0.1:<openclaw-port>

# 特定パスのみ公開
tailscale serve https /api http://127.0.0.1:8080

# TCP転送
tailscale serve tcp:2222 tcp://localhost:22

# 静的ファイル公開
tailscale serve https / /path/to/static/files

# 現在の公開設定を確認
tailscale serve status

# 設定をリセット（全て停止）
tailscale serve reset

# 特定サービスを停止
tailscale serve https / off
```

### ServeとFunnelの違い

| 機能 | アクセス範囲 | 用途 |
|------|-------------|------|
| **Serve** | tailnet内のみ | 開発サーバー、管理ツール（OpenClaw等） |
| **Funnel** | インターネット全体 | Webhook受信、外部公開 |

---

## Tailscale Funnel（インターネット公開）

**注意**: Funnelはインターネット全体から接続可能。機密サービスには使用しない。

```bash
# インターネット公開（要tailscale.com管理コンソールでの許可）
tailscale funnel https / http://127.0.0.1:8080

# 公開状態確認
tailscale funnel status

# 停止
tailscale funnel reset
```

---

## SSH関連

```bash
# Tailscale SSH（opensshが不要、tailscale管理のSSH）
tailscale ssh <username>@<server-hostname>

# ファイル転送（Taildrop）
tailscale file cp ./file.txt <server-hostname>:

# 受信待ちリスト確認
tailscale file get
```

---

## デバイス管理（CLI）

```bash
# 接続済みデバイス一覧（詳細）
tailscale status --peers

# 特定デバイスの詳細
tailscale status --json | jq '.Peer[] | select(.HostName == "<server-hostname>")'

# デバイスのTailscale IP取得
tailscale status --json | jq -r '.Peer[] | select(.HostName == "<server-hostname>") | .TailscaleIPs[0]'
```

---

## Tailscale ローカルAPI（上級者向け）

Tailscale CLIは `http://localhost:41112` でローカルAPIを提供。

```bash
# ステータス取得（生の局所API）
curl -s --unix-socket /var/run/tailscale/tailscaled.sock http://local-tailscaled.sock/localapi/v0/status | jq .

# macOSの場合
curl -s http://localhost:41112/localapi/v0/status | jq .

# ピア一覧
curl -s http://localhost:41112/localapi/v0/status | jq '.Peer | to_entries[] | {name: .value.HostName, ip: .value.TailscaleIPs[0]}'
```

---

## Tailscale Admin API（クラウド管理）

環境変数 `TAILSCALE_API_KEY` が必要。

```bash
export TAILSCALE_API_KEY="tskey-api-..."
export TAILSCALE_TAILNET="<tailnet-name>"

# デバイス一覧
curl -H "Authorization: Bearer $TAILSCALE_API_KEY" \
  "https://api.tailscale.com/api/v2/tailnet/$TAILSCALE_TAILNET/devices" | jq .

# 特定デバイスの情報
curl -H "Authorization: Bearer $TAILSCALE_API_KEY" \
  "https://api.tailscale.com/api/v2/device/<DEVICE_ID>" | jq .

# デバイスを認可
curl -X POST -H "Authorization: Bearer $TAILSCALE_API_KEY" \
  "https://api.tailscale.com/api/v2/device/<DEVICE_ID>/authorized" \
  -H "Content-Type: application/json" -d '{"authorized": true}'

# キーの作成
curl -X POST -H "Authorization: Bearer $TAILSCALE_API_KEY" \
  "https://api.tailscale.com/api/v2/tailnet/$TAILSCALE_TAILNET/keys" \
  -H "Content-Type: application/json" \
  -d '{"capabilities": {"devices": {"create": {"reusable": true, "preauthorized": true}}}}'
```

---

## macOS固有

```bash
# Tailscaled状態確認
sudo launchctl list | grep tailscale

# ログ確認（macOS）
log stream --predicate 'subsystem == "com.tailscale.ipn.macsys"' --level debug

# 設定ファイルの場所
ls ~/Library/Preferences/io.tailscale.ipn.macos.plist
```
