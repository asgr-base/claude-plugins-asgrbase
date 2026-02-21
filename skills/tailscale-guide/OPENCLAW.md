# OpenClaw × Tailscale 連携ガイド

> **プレースホルダー凡例**
> - `<username>` : サーバーのSSHユーザー名
> - `<tailscale-ip>` : サーバーのTailscale IP
> - `<server-hostname>` : Tailscale管理画面に表示されるホスト名
> - `<tailnet-name>` : tailnetのドメイン名（`.ts.net` の前の部分）
> - `<your-token>` : OpenClawのアクセストークン
> - `<openclaw-port>` : OpenClaw Gatewayのポート番号（デフォルト: 18789）
> - `<plist-name>` : LaunchAgentのplistファイル名（例: `com.yourname.openclaw-gateway`）

## アーキテクチャ概要

```
[開発機（MacBook / iPhone等）]
       │
       │ Tailscale VPN (暗号化)
       │
[サーバー機（Mac mini等）]
       │
       ├── Tailscale Serve (:443 HTTPS)
       │         │
       │         └──→ localhost:<openclaw-port> (OpenClaw Gateway)
       │
       └── OpenClaw Gateway (127.0.0.1:<openclaw-port>)
                 │
                 ├── Telegram Bot
                 └── Claude AI 連携
```

**セキュリティ原則**:
- OpenClawは `127.0.0.1:<openclaw-port>` にバインド（外部直接接続不可）
- Tailscale ServeがHTTPS終端・tailnet内転送
- トークン認証で二重保護

---

## OpenClaw Web UIへのアクセス

### 方法1: Tailscale Serve（通常利用）

ブラウザで以下のURLを開く：

```
https://<server-hostname>.<tailnet-name>.ts.net/?token=<your-token>
```

**前提条件**:
- 開発機がTailscaleに接続済み
- サーバーのTailscale Serveが起動済み

サーバー側でServeの確認：
```bash
ssh <username>@<tailscale-ip> 'tailscale serve status'
```

### 方法2: SSHポートフォワーディング（デバッグ用）

```bash
# サーバーのOpenClawをローカルポート18790に転送
ssh -L 18790:localhost:<openclaw-port> <username>@<tailscale-ip> -N &

# ブラウザで http://localhost:18790 にアクセス
open "http://localhost:18790/?token=<your-token>"
```

SSHポートフォワーディングを終了：
```bash
# バックグラウンドのSSHプロセスを終了
kill %1
# またはPIDで指定
ps aux | grep 'ssh -L 18790' | grep -v grep | awk '{print $2}' | xargs kill
```

---

## OpenClaw Gateway の管理（SSH経由）

### ヘルスチェック

```bash
ssh <username>@<tailscale-ip> << 'EOF'
# プロセス確認
ps aux | grep openclaw | grep -v grep

# ヘルスエンドポイント
curl -s http://localhost:<openclaw-port>/health | jq .

# ポート確認
lsof -i :<openclaw-port>
EOF
```

### サービスの再起動

```bash
ssh <username>@<tailscale-ip> << 'EOF'
# LaunchAgentのリロード
launchctl unload ~/Library/LaunchAgents/<plist-name>.plist
sleep 2
launchctl load ~/Library/LaunchAgents/<plist-name>.plist

# 状態確認
launchctl list | grep openclaw
EOF
```

### ログ確認

```bash
ssh <username>@<tailscale-ip> << 'EOF'
# 最新のゲートウェイログ
tail -n 50 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log

# エラーのみ抽出
grep -i "error\|warn\|fail" /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | tail -20
EOF
```

---

## Tailscale Serve の設定・管理

### 現在の設定を確認（サーバー上）

```bash
ssh <username>@<tailscale-ip> 'tailscale serve status'
```

期待される出力：
```
# Output example:
https://<server-hostname>.<tailnet-name>.ts.net
|-- / proxy http://127.0.0.1:<openclaw-port>
```

### Serveが停止している場合の復旧

```bash
ssh <username>@<tailscale-ip> << 'EOF'
# OpenClawをtailnet内に再公開
tailscale serve https / http://127.0.0.1:<openclaw-port>

# 確認
tailscale serve status
EOF
```

---

## 電源スケジュール設定（オプション）

Mac mini等のサーバーをスケジュールで管理する場合の例：

| 時刻 | 動作 | スクリプト例 |
|------|------|-----------|
| 任意（朝） | スリープ無効（稼働モード） | `start-daytime.sh` |
| 任意（夜） | スリープ有効（省電力モード） | `start-nighttime.sh` |

### LaunchDaemon の状態確認

```bash
ssh <username>@<tailscale-ip> << 'EOF'
# LaunchDaemonの一覧
sudo launchctl list | grep <bundle-prefix>

# plist確認
ls -la /Library/LaunchDaemons/*.plist
EOF
```

---

## OpenClaw の設定ファイル

```bash
# 設定ファイルを表示（サーバー上）
ssh <username>@<tailscale-ip> 'cat ~/.openclaw/openclaw.json'

# セッション情報
ssh <username>@<tailscale-ip> 'cat ~/.openclaw/agents/main/sessions/sessions.json | jq .'
```

### 重要な設定項目

```json
{
  "gateway": {
    "port": 18789,
    "host": "127.0.0.1",   // ← ローカルバインド（重要）
    "auth": {
      "mode": "token"       // ← トークン認証
    }
  }
}
```

---

## トラブルシューティング

### OpenClaw Web UIにつながらない

**確認手順**:
1. 開発機のTailscale接続を確認: `tailscale status`
2. サーバーへのping: `tailscale ping <server-hostname>`
3. Serveの状態を確認: `ssh <username>@<tailscale-ip> 'tailscale serve status'`
4. OpenClawプロセスを確認: `ssh <username>@<tailscale-ip> 'ps aux | grep openclaw'`

### WebSocket接続エラー（1008: pairing required）

Chromeブラウザの別プロファイル使用時に発生することがある（デバイスIDが異なるため）。

**解決策**:
- 同じChromeプロファイルを使用する
- またはChrome Canaryを試す
- またはSSHポートフォワーディング方式でアクセス

### Ollama fetch失敗のログエラー

OpenClawがOllamaサービスに接続できない場合のエラー。OpenClaw自体の動作には影響しない（正常動作中でも表示される場合がある）。

```bash
# Ollamaの状態確認
ssh <username>@<tailscale-ip> 'curl -s http://localhost:11434/api/tags | jq .'
```

---

## よく使うワンライナー集

```bash
# サーバーの状態を一括確認
ssh <username>@<tailscale-ip> '
echo "=== Tailscale ==="
tailscale status
echo ""
echo "=== OpenClaw Serve ==="
tailscale serve status
echo ""
echo "=== OpenClaw Health ==="
curl -s http://localhost:<openclaw-port>/health
echo ""
echo "=== OpenClaw Process ==="
ps aux | grep openclaw | grep -v grep
'

# サーバーを経由してOpenClaw APIを叩く
ssh <username>@<tailscale-ip> 'curl -s http://localhost:<openclaw-port>/health | jq .'

# ログのリアルタイム監視
ssh <username>@<tailscale-ip> "tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log"
```
