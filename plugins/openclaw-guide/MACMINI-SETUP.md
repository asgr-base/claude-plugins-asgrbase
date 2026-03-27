# Mac mini × OpenClaw セットアップガイド

Mac mini（Apple Silicon）を常時稼働サーバーとして OpenClaw Gateway を運用する構成のセットアップ手順。

## 前提条件

- Mac mini（Apple Silicon、macOS Sonoma 以降推奨）
- Homebrew インストール済み
- Node.js v22 以上（`node --version` で確認）
- Tailscale インストール済み（リモートアクセスを使う場合）

---

## 1. OpenClaw インストール

```bash
# Homebrew 経由でインストール
brew install openclaw

# インストール確認
openclaw --version

# セットアップウィザードを実行（初回のみ）
openclaw setup
```

`openclaw setup` でインタラクティブに設定（ポート、トークン、エージェント等）が生成される。

---

## 2. LaunchAgent の設定（自動起動）

`openclaw setup` 実行後、LaunchAgent plist が `~/Library/LaunchAgents/` に自動生成される。

```bash
# plist ファイルの確認
ls ~/Library/LaunchAgents/ | grep openclaw

# LaunchAgent を有効化（ログイン時に自動起動）
PLIST=$(ls ~/Library/LaunchAgents/ | grep openclaw | head -1)
launchctl load ~/Library/LaunchAgents/$PLIST

# 起動確認（3秒待つ）
sleep 3
ps aux | grep openclaw | grep -v grep
curl -s http://localhost:18789/health && echo "OK"
```

---

## 3. Tailscale Serve 設定（リモートアクセス）

Mac mini の OpenClaw Gateway を tailnet 内の他デバイスから HTTPS でアクセスできるようにする。

```bash
# OpenClaw Gateway を tailnet 内に HTTPS で公開
tailscale serve https / http://127.0.0.1:18789

# 設定確認
tailscale serve status
# 期待出力例:
# https://<hostname>.tailnet-name.ts.net
# |-- / proxy http://127.0.0.1:18789
```

これにより `https://<hostname>.tailnet-name.ts.net/?token=<your-token>` でアクセス可能になる。

### Tailscale Serve の永続化

OpenClaw の設定ファイルに `tailscale.resetOnExit: false` を追加すると、Gateway 再起動後も Serve 設定が維持される。

```bash
openclaw config set gateway.tailscale.resetOnExit false
```

---

## 4. スリープ管理（24時間稼働）

Mac mini を常時稼働させるには、スリープ設定を調整する必要がある。

### システム環境設定で設定（GUI）

「システム設定」→「省エネルギー」→ 電源アダプター接続時のスリープ無効化

### コマンドラインで設定

```bash
# スリープを無効化（電源接続時）
sudo pmset -c sleep 0 disksleep 0

# ディスプレイスリープのみ許可（ディスプレイなし運用向け）
sudo pmset -c displaysleep 30

# 現在の設定確認
pmset -g
```

### 時間帯スケジュールで管理（省電力運用）

夜間はスリープを許可し、昼間のみスリープ無効にする運用例：

**昼間モード用スクリプト** (`~/start-daytime.sh`):

```bash
#!/bin/bash
# 昼間モード: スリープ無効
sudo pmset -c sleep 0 disksleep 0
```

**夜間モード用スクリプト** (`~/start-nighttime.sh`):

```bash
#!/bin/bash
# 夜間モード: スリープを許可
sudo pmset -c sleep 30 disksleep 10
```

**LaunchDaemon で自動実行**（例：7:00 AM 昼間モード開始、1:00 AM 夜間モード開始）:

```xml
<!-- /Library/LaunchDaemons/com.<yourname>.disable-sleep.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.<yourname>.disable-sleep</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/<username>/start-daytime.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

```bash
# LaunchDaemon を登録
sudo launchctl load /Library/LaunchDaemons/com.<yourname>.disable-sleep.plist
```

---

## 5. SSH リモートアクセス設定

Mac mini へのリモート操作のため、SSH（リモートログイン）を有効化する。

```bash
# Remote Login を有効化
sudo systemsetup -setremotelogin on

# 確認
sudo systemsetup -getremotelogin
# → Remote Login: On

# 接続テスト（Tailscale 経由）
ssh <username>@<tailscale-ip>
```

---

## 6. セットアップ確認チェックリスト

```bash
echo "=== OpenClaw プロセス ==="
ps aux | grep openclaw | grep -v grep || echo "Not running"

echo ""
echo "=== ポート 18789 ==="
lsof -i :18789 | grep LISTEN || echo "Not listening"

echo ""
echo "=== ヘルスチェック ==="
curl -sf http://localhost:18789/health && echo "OK" || echo "FAILED"

echo ""
echo "=== LaunchAgent 状態 ==="
launchctl list | grep openclaw || echo "Not loaded"

echo ""
echo "=== Tailscale Serve ==="
tailscale serve status

echo ""
echo "=== スリープ設定 ==="
pmset -g | grep -E "sleep|disksleep"
```

---

## 7. SSH 経由でのリモート管理

```bash
# ヘルスチェック一括確認
ssh <username>@<tailscale-ip> << 'EOF'
echo "=== OpenClaw Health ==="
curl -s http://localhost:18789/health | jq .

echo ""
echo "=== Tailscale Serve ==="
tailscale serve status

echo ""
echo "=== OpenClaw Process ==="
ps aux | grep openclaw | grep -v grep
EOF

# OpenClaw 再起動（LaunchAgent 経由）
ssh <username>@<tailscale-ip> << 'EOF'
PLIST=$(ls ~/Library/LaunchAgents/ | grep openclaw | head -1)
launchctl unload ~/Library/LaunchAgents/$PLIST
sleep 2
launchctl load ~/Library/LaunchAgents/$PLIST
sleep 3
curl -s http://localhost:18789/health && echo "OK"
EOF

# ログのリアルタイム監視
ssh <username>@<tailscale-ip> "tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log"
```

---

## 8. トラブルシューティング

Mac mini 固有のトラブルについては [TROUBLESHOOTING.md](TROUBLESHOOTING.md) も参照。

### SSH 接続できない

```bash
# Tailscale 接続確認
tailscale status
tailscale ping <device-name>

# Mac mini がスリープしていないか確認
# → Tailscale 管理コンソール（https://login.tailscale.com/admin/machines）で Last seen を確認
```

### OpenClaw が自動起動しない

```bash
# LaunchAgent のロードを確認
launchctl list | grep openclaw

# 手動でロード
PLIST=$(ls ~/Library/LaunchAgents/ | grep openclaw | head -1)
launchctl load ~/Library/LaunchAgents/$PLIST
```

### ポートが占有されている（ゾンビプロセス）

→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md) の「Gateway 起動しない」セクションを参照。
