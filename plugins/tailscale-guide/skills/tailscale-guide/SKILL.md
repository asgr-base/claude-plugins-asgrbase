---
name: tailscale-guide
description: Tailscaleネットワークの管理・操作ガイド。デバイス確認、SSH接続、Tailscale Serve設定、OpenClawとの連携を支援。tailscale、tailnet、VPN、リモートサーバー接続、OpenClawリモートアクセス、SSH経由の操作関連の質問時に使用。
version: 1.0.0
author: claude_code
createDate: 2026-02-18
updateDate: 2026-02-18
license: Apache-2.0
disable-model-invocation: true
---

# Tailscale Guide

Tailscaleはゼロコンフィグのメッシュ型VPN。開発機とサーバー機をセキュアに接続し、OpenClaw Gatewayへのリモートアクセスを提供する。

## クイックリファレンス

| やりたいこと | コマンド / 操作 |
|-------------|----------------|
| ネットワーク状態確認 | `tailscale status` |
| 自分のTailscale IP確認 | `tailscale ip` |
| サーバーにSSH接続 | `ssh <username>@<tailscale-ip>` |
| OpenClaw Web UIを開く | ブラウザで `https://<server-hostname>.<tailnet-name>.ts.net/?token=<your-token>` |
| Tailscale Serve状態確認 | `tailscale serve status` |
| デバイス一覧（詳細） | [COMMANDS.md](COMMANDS.md) |
| OpenClaw連携 | [OPENCLAW.md](OPENCLAW.md) |
| トラブルシューティング | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |

## 環境設定（構成例）

```
開発機（MacBook等）
  └── Tailscale IP: 動的（tailnet内で解決）
  └── Claude Code実行環境

サーバー機（Mac mini等）
  └── Tailscale IP: <tailscale-ip>
  └── ホスト名: <server-hostname>.<tailnet-name>.ts.net
  └── OpenClaw Gateway: localhost:<openclaw-port>
  └── Tailscale Serve: HTTPS → localhost:<openclaw-port>
```

> **プレースホルダー凡例**
> - `<username>` : サーバーのSSHユーザー名
> - `<tailscale-ip>` : サーバーのTailscale IP（`tailscale ip` で確認）
> - `<server-hostname>` : Tailscale管理画面に表示されるホスト名
> - `<tailnet-name>` : tailnetのドメイン名（`.ts.net` の前の部分）
> - `<your-token>` : OpenClawのアクセストークン
> - `<openclaw-port>` : OpenClaw Gatewayのポート番号（デフォルト: 18789）

## よく使うコマンド

### 状態確認

```bash
# ネットワーク状態とピア一覧
tailscale status

# 自分のTailscale IPアドレス
tailscale ip

# 接続中のピアをping
tailscale ping <server-hostname>

# バージョン確認
tailscale version
```

### SSH接続（サーバーへ）

```bash
# Tailscale IP経由（推奨）
ssh <username>@<tailscale-ip>

# ホスト名経由
ssh <username>@<server-hostname>.<tailnet-name>.ts.net

# SSHポートフォワーディング（OpenClawをローカルでアクセス）
ssh -L 18790:localhost:<openclaw-port> <username>@<tailscale-ip>
# → ブラウザで http://localhost:18790 でOpenClawにアクセス可能
```

### Tailscale Serve（サービス公開）

```bash
# サーバー側: OpenClawをtailnet内に公開
tailscale serve https / http://127.0.0.1:<openclaw-port>

# 公開状態を確認
tailscale serve status

# 公開を停止
tailscale serve reset
```

## OpenClaw + Tailscale 連携

### アクセス方法

| 方式 | URL/コマンド | 用途 |
|------|-------------|------|
| **Tailscale Serve（推奨）** | `https://<server-hostname>.<tailnet-name>.ts.net/?token=<your-token>` | ブラウザアクセス |
| **SSHポートフォワーディング** | `ssh -L 18790:localhost:<openclaw-port> <username>@<tailscale-ip>` | CLIデバッグ |
| **直接SSH** | `ssh <username>@<tailscale-ip>` | サーバー操作 |

**詳細**: [OPENCLAW.md](OPENCLAW.md)

## セキュリティ原則

- OpenClaw GatewayはサーバーのローカルIP（`127.0.0.1`）にバインド（外部直接アクセス不可）
- Tailscale Serveを通じてtailnet内のデバイスのみがアクセス可能
- トークン認証（`?token=...`）で二重保護
- `0.0.0.0` でのバインドは**絶対に避ける**

## 参照ファイル

| ファイル | 内容 |
|----------|------|
| [COMMANDS.md](COMMANDS.md) | CLI コマンド完全リファレンス |
| [OPENCLAW.md](OPENCLAW.md) | OpenClaw × Tailscale 連携詳細 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 接続問題のデバッグ手順 |
