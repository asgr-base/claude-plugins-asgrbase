# Tailscale トラブルシューティング

> **プレースホルダー凡例**
> - `<username>` : サーバーのSSHユーザー名
> - `<tailscale-ip>` : サーバーのTailscale IP
> - `<server-hostname>` : Tailscale管理画面に表示されるホスト名
> - `<tailnet-name>` : tailnetのドメイン名
> - `<openclaw-port>` : OpenClaw Gatewayのポート番号（デフォルト: 18789）
> - `<plist-name>` : LaunchAgentのplistファイル名

## 症状別クイックガイド

| 症状 | 原因の可能性 | ジャンプ先 |
|------|-------------|-----------|
| SSH接続タイムアウト | Tailscale未接続 / サーバースリープ | [#ssh-接続できない](#ssh-接続できない) |
| OpenClaw Web UIにアクセスできない | Serve停止 / OpenClaw停止 | [#openclaw-にアクセスできない](#openclaw-にアクセスできない) |
| 接続タイムアウト（HTTPS） | Tailscale Serve停止 | [#tailscale-serve-が動かない](#tailscale-serve-が動かない) |
| `tailscale ping` が失敗 | VPN未接続 / ルーティング問題 | [#ping-が通らない](#ping-が通らない) |

---

## SSH 接続できない

### 症状
```
ssh: connect to host <tailscale-ip> port 22: Connection timed out
```

### 確認手順

```bash
# 1. Tailscale接続状態を確認
tailscale status

# 2. サーバーへのpingを試行
tailscale ping <server-hostname>

# 3. 接続できない場合、サーバーがスリープしていないか確認（Tailscaleの管理コンソールで確認）
# https://login.tailscale.com/admin/machines → <server-hostname> の "Last seen"

# 4. ローカルネットワーク経由で試行（同一ネットワークの場合）
ssh <username>@<server-hostname>.local
```

### 解決策

**A. Tailscale未接続の場合**:
```bash
tailscale up
tailscale status  # 再確認
```

**B. サーバーがスリープしている場合**:
- Wake on LANが設定済みなら: `wakeonlan <MAC_ADDRESS>`
- 物理的に起こす（ディスプレイを接続するかキーボード入力）
- スリープ設定を見直す（macOS: システム設定 → ディスプレイ → スリープ）

**C. Tailscaleは接続されているがSSHが失敗する場合**:
```bash
# SSH詳細ログで確認
ssh -v <username>@<tailscale-ip>

# sshd が起動しているか（サーバーのコンソールで）
sudo launchctl list | grep ssh
sudo systemsetup -getremotelogin  # Remote Login の状態
```

---

## OpenClaw にアクセスできない

### 症状
- ブラウザでURLを開くと「接続できません」や「タイムアウト」

### 確認手順（SSHでサーバーに入る）

```bash
ssh <username>@<tailscale-ip> << 'EOF'
echo "=== 1. Tailscale Serve 状態 ==="
tailscale serve status

echo ""
echo "=== 2. OpenClaw プロセス ==="
ps aux | grep openclaw | grep -v grep

echo ""
echo "=== 3. ポート <openclaw-port> のリスン確認 ==="
lsof -i :<openclaw-port>

echo ""
echo "=== 4. OpenClaw ヘルスチェック ==="
curl -sf http://localhost:<openclaw-port>/health && echo "OK" || echo "FAILED"
EOF
```

### 解決策

**A. Tailscale Serveが停止している場合**:
```bash
ssh <username>@<tailscale-ip> << 'EOF'
tailscale serve https / http://127.0.0.1:<openclaw-port>
tailscale serve status
EOF
```

**B. OpenClawが停止している場合**:
```bash
ssh <username>@<tailscale-ip> << 'EOF'
# ゾンビプロセスがある場合は先に終了
ps aux | grep openclaw | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null

# LaunchAgentの再起動
launchctl unload ~/Library/LaunchAgents/<plist-name>.plist
sleep 2
launchctl load ~/Library/LaunchAgents/<plist-name>.plist
sleep 3

# 確認
ps aux | grep openclaw | grep -v grep
curl -sf http://localhost:<openclaw-port>/health && echo "OpenClaw OK" || echo "OpenClaw FAILED"
EOF
```

**C. ポートが別プロセスに占有されている場合**:
```bash
ssh <username>@<tailscale-ip> << 'EOF'
# ポートを使っているプロセスを確認
lsof -ti :<openclaw-port>

# 強制終了（慎重に）
lsof -ti :<openclaw-port> | xargs kill -9

# ロックファイルの削除（必要な場合）
rm -f ~/.openclaw/*.lock

# openclaw doctor で修復
openclaw doctor --fix
EOF
```

---

## Tailscale Serve が動かない

### 症状
`tailscale serve status` で何も表示されない、またはHTTPSアクセスが失敗する。

### 確認と復旧

```bash
ssh <username>@<tailscale-ip> << 'EOF'
# 現在の設定を確認
tailscale serve status

# Tailscale自体の状態
tailscale status

# Serveを再設定
tailscale serve reset  # 一旦クリア
tailscale serve https / http://127.0.0.1:<openclaw-port>  # 再設定

# 確認
tailscale serve status
curl -I https://<server-hostname>.<tailnet-name>.ts.net/health
EOF
```

---

## Ping が通らない

### 症状
```bash
tailscale ping <server-hostname>
# → ping timeout
```

### 確認手順

```bash
# 1. Tailscaleの接続状態
tailscale status

# 2. ネットワーク診断
tailscale netcheck

# 3. DERP（中継サーバー）経由での接続確認
tailscale ping --verbose <server-hostname>
```

### 解決策

**A. Tailscale再起動（開発機側）**:
```bash
# macOS
sudo launchctl stop com.tailscale.ipn.macsys && sleep 2 && sudo launchctl start com.tailscale.ipn.macsys
# またはmenubarアイコンから再起動
```

**B. Tailscale再認証**:
```bash
tailscale logout
tailscale login
```

**C. DERPリレー経由になっている場合**（直接接続にしたい場合）:
- ファイアウォール設定でUDP 41641ポートを開放する
- `tailscale netcheck` でNATタイプを確認

---

## OpenClaw 設定の問題

### 無効な設定キーエラー

```bash
ssh <username>@<tailscale-ip> << 'EOF'
# 設定を修復（無効なキーを自動除去）
openclaw doctor --fix

# 設定の確認
cat ~/.openclaw/openclaw.json | jq .
EOF
```

**除去される無効なキー**: `cache`, `heartbeat`, `rate_limits`, `budgets`, `_meta`

---

## ログ収集（サポート用）

```bash
ssh <username>@<tailscale-ip> << 'EOF'
echo "=== System Info ==="
sw_vers
date

echo ""
echo "=== Tailscale Status ==="
tailscale status --json | jq '{self: .Self, peers: (.Peer | length)}'

echo ""
echo "=== OpenClaw Version ==="
openclaw --version 2>/dev/null || echo "openclaw CLI not found"

echo ""
echo "=== Recent Errors in Log ==="
grep -i "error\|panic\|fatal" /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | tail -20

echo ""
echo "=== Port Status ==="
lsof -i :<openclaw-port>
EOF
```
