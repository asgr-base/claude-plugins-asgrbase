# Happy Mobile Client - トラブルシューティング

## 目次

- [インストール関連の問題](#インストール関連の問題)
- [接続の問題](#接続の問題)
- [認証の問題](#認証の問題)
- [パフォーマンスの問題](#パフォーマンスの問題)
- [モバイルアプリの問題](#モバイルアプリの問題)
- [エラーメッセージ](#エラーメッセージ)

## インストール関連の問題

### npm install -g happy-coder が失敗する

**症状**: インストール時にエラーが発生

**原因と解決策**:

1. **権限エラー（EACCES）**
```bash
# グローバルインストールの権限がない場合
sudo npm install -g happy-coder

# または、npm設定を変更（推奨）
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
npm install -g happy-coder
```

2. **Node.jsバージョンが古い**
```bash
# Node.jsバージョンを確認
node --version

# 推奨: v18以上
# nvmを使用してアップデート
nvm install 18
nvm use 18
npm install -g happy-coder
```

3. **ネットワークエラー**
```bash
# プロキシ設定を確認
npm config get proxy
npm config get https-proxy

# プロキシをクリア
npm config delete proxy
npm config delete https-proxy

# npmレジストリを変更
npm config set registry https://registry.npmjs.org/
```

### happy コマンドが見つからない

**症状**: `happy: command not found`

**解決策**:

```bash
# PATHを確認
echo $PATH

# npmのグローバルbinディレクトリを確認
npm bin -g

# パスを追加（zshの場合）
echo 'export PATH="$(npm bin -g):$PATH"' >> ~/.zshrc
source ~/.zshrc

# パスを追加（bashの場合）
echo 'export PATH="$(npm bin -g):$PATH"' >> ~/.bash_profile
source ~/.bash_profile
```

## 接続の問題

### QRコードが表示されない

**症状**: `happy` 実行時にQRコードが表示されない

**診断手順**:

```bash
# 1. Claude Codeの認証を確認
claude auth status

# 2. ターミナルの文字エンコーディングを確認
echo $LANG

# 3. デバッグモードで実行
happy --verbose

# 4. ログを確認
cat ~/.happy/logs/happy.log
```

**解決策**:

```bash
# Claude Codeを再認証
claude auth logout
claude auth login

# happyを再インストール
npm uninstall -g happy-coder
npm cache clean --force
npm install -g happy-coder

# 別のターミナルエミュレータで試す
# iTerm2, Terminal.app, Hyper等
```

### モバイルアプリから接続できない

**症状**: QRコードをスキャンしても接続が確立されない

**チェックリスト**:

1. **ネットワーク接続**
```bash
# インターネット接続を確認
ping google.com

# Happyサーバーへの接続を確認
curl https://happy.engineering/health
```

2. **ファイアウォール設定**
```bash
# macOSファイアウォール設定を確認
# システム設定 > ネットワーク > ファイアウォール
# Happyの通信を許可

# ポート開放状況を確認
lsof -i -P | grep happy
```

3. **VPN/プロキシの影響**
```bash
# VPNを一時的に無効化して試す
# プロキシ設定を確認
env | grep -i proxy
```

**解決策**:

```bash
# 1. Happyプロセスを完全終了
pkill -f happy

# 2. キャッシュをクリア
rm -rf ~/.happy/cache

# 3. 再起動
happy --reset
```

### 接続が頻繁に切れる

**症状**: セッション中に接続が切断される

**原因**:
- 不安定なネットワーク
- タイムアウト設定が短すぎる
- システムリソース不足

**解決策**:

```bash
# タイムアウトを延長
export HAPPY_TIMEOUT=120000  # 2分

# Keep-Aliveを有効化
happy --keep-alive

# 接続品質を確認
ping -c 10 8.8.8.8
```

## 認証の問題

### Claude Code認証エラー

**症状**: `Not authenticated` エラー

**解決策**:

```bash
# 現在の認証状態を確認
claude auth status

# 認証情報をクリア
claude auth logout

# 再認証
claude auth login

# 認証ファイルの確認
ls -la ~/.claude/
```

### セッショントークンが無効

**症状**: `Invalid session token` エラー

**解決策**:

```bash
# 全セッションを無効化
happy --revoke-all

# 新しいセッションを開始
happy

# セッション情報を確認
happy --list-sessions
```

### 鍵の不整合

**症状**: `Key mismatch` または `Decryption failed` エラー

**解決策**:

```bash
# 暗号化鍵を再生成
happy --regenerate-keys

# 古い鍵ファイルをバックアップして削除
mv ~/.happy/private_key.enc ~/.happy/private_key.enc.bak
mv ~/.happy/public_key.pem ~/.happy/public_key.pem.bak

# Happyを再起動（新しい鍵が生成される）
happy
```

## パフォーマンスの問題

### 応答が遅い

**症状**: コマンド実行に時間がかかる

**診断**:

```bash
# システムリソースを確認
top -l 1 | head -n 10

# Happyプロセスのリソース使用を確認
ps aux | grep happy

# ネットワーク遅延を確認
ping -c 10 happy.engineering
```

**解決策**:

```bash
# メモリを増やす
export NODE_OPTIONS="--max-old-space-size=4096"

# 圧縮を有効化
happy --enable-compression

# キャッシュを有効化
happy --enable-cache

# 不要なプロセスを終了
pkill -f "unnecessary-process"
```

### メモリ使用量が多い

**症状**: Happyが大量のメモリを消費

**解決策**:

```bash
# メモリ最適化モードで起動
happy --optimize-memory

# セッション履歴を制限
happy --max-history 100

# 定期的にキャッシュをクリア
rm -rf ~/.happy/cache/*

# ガベージコレクションを強制
kill -USR2 $(pgrep -f happy)
```

### CPU使用率が高い

**症状**: Happyが常にCPUを使用している

**診断**:

```bash
# CPU使用状況を詳しく確認
top -pid $(pgrep happy)

# Node.jsプロファイラを有効化
happy --prof
```

**解決策**:

```bash
# アイドルタイムアウトを設定
happy --idle-timeout 300000  # 5分

# バックグラウンドタスクを制限
happy --no-background-tasks

# プロセス優先度を下げる
renice -n 10 $(pgrep happy)
```

## モバイルアプリの問題

### アプリがクラッシュする

**症状**: Happyアプリが突然終了する

**解決策**:

1. **アプリを再インストール**
   - アプリを削除
   - App Store/Google Playから再インストール

2. **キャッシュをクリア**
   - iOS: 設定 > Happy > データを削除
   - Android: 設定 > アプリ > Happy > ストレージ > キャッシュを削除

3. **OSを更新**
   - iOS: 設定 > 一般 > ソフトウェアアップデート
   - Android: 設定 > システム > システムアップデート

### 音声入力が機能しない

**症状**: 音声コーディング・Voice Agentが使えない

**Voice Agentの技術構成**:
- STT（音声→テキスト）: Eleven Labs（クラウド処理）
- TTS（テキスト→音声）: Eleven Labs（クラウド処理）
- 中間処理: Claude Sonnet 4（Voice Agent）

**チェックリスト**:

1. **マイクの権限**
   - iOS: 設定 > Happy > マイク > 許可
   - Android: 設定 > アプリ > Happy > 権限 > マイク
2. **インターネット接続（必須）**
   - STT/TTSはEleven Labs経由のためオフラインでは動作しない
   - Wi-Fi/モバイルデータ接続を確認
3. **言語設定**
   - アプリ内設定で正しい言語を選択（日本語/英語）
4. **音声読み上げ（TTS）が聞こえない場合**
   - スマホの音量を確認
   - サイレントモード/マナーモードを解除
   - Bluetooth接続デバイスの確認

**解決策**:

```bash
# マイクデバイスを確認（macOS側で問題切り分け）
system_profiler SPAudioDataType

# ネットワーク接続を確認
ping google.com

# Happyを再起動
pkill -f happy && happy
```

### プッシュ通知が届かない

**症状**: タスク完了やエラー時に通知が来ない

**解決策**:

1. **通知権限を確認**
   - iOS: 設定 > 通知 > Happy > 通知を許可
   - Android: 設定 > アプリ > Happy > 通知

2. **Do Not Disturb モードを確認**
   - iOS: コントロールセンターで確認
   - Android: クイック設定で確認

3. **アプリ内設定を確認**
   - Happy アプリ > 設定 > 通知 > すべて有効

## エラーメッセージ

### "Failed to start Happy server"

**原因**: ポート競合またはプロセスが既に実行中

**解決策**:

```bash
# 既存のHappyプロセスを終了
pkill -f happy

# ポート使用状況を確認
lsof -i -P | grep LISTEN

# 別のポートで起動
happy --port 8081
```

### "Encryption key not found"

**原因**: 暗号化鍵ファイルが削除または破損

**解決策**:

```bash
# 鍵を再生成
happy --regenerate-keys

# バックアップから復元（存在する場合）
cp ~/.happy/backup/private_key.enc ~/.happy/
cp ~/.happy/backup/public_key.pem ~/.happy/
```

### "Claude CLI not found"

**原因**: Claude CLIがインストールされていない

**解決策**:

```bash
# Claude CLIをインストール
# macOS
brew install claude-ai/claude/claude

# または公式サイトからダウンロード
# https://claude.ai/download
```

### "Connection timeout"

**原因**: ネットワーク問題またはサーバー応答なし

**解決策**:

```bash
# ネットワーク診断
ping google.com
traceroute happy.engineering

# DNS設定を確認
scutil --dns

# タイムアウトを延長
happy --timeout 60000
```

### "Session expired"

**原因**: セッショントークンの有効期限切れ

**解決策**:

```bash
# 新しいセッションを開始
happy --new-session

# 自動更新を有効化
happy --auto-refresh-token
```

## デバッグツール

### 診断レポートの生成

```bash
# 完全な診断レポートを生成
happy --diagnose > ~/happy-diagnostic-report.txt

# レポート内容:
# - システム情報
# - インストール状態
# - ネットワーク状態
# - ログファイル抜粋
```

### ログの詳細表示

```bash
# リアルタイムログ表示
tail -f ~/.happy/logs/happy.log

# エラーログのみ表示
grep ERROR ~/.happy/logs/happy.log

# 最近のログを表示
tail -n 100 ~/.happy/logs/happy.log
```

### ネットワークトレース

```bash
# ネットワーク通信をトレース
happy --trace-network

# パケットキャプチャ（要sudo）
sudo tcpdump -i any -w happy-traffic.pcap port 8080
```

## サポートリソース

問題が解決しない場合：

1. **公式ドキュメントを確認**
   - https://happy.engineering/docs/troubleshooting/

2. **GitHub Issuesを検索**
   - https://github.com/slopus/happy/issues

3. **新しいIssueを作成**
   - 診断レポートを添付
   - 再現手順を詳しく記載
   - 環境情報（OS、Node.jsバージョン等）を含める

4. **コミュニティに質問**
   - Discord / Slack / フォーラム
   - Stack Overflow（タグ: `happy-coder`）

## クイックフィックス

よくある問題の即座の解決策：

```bash
# 完全リセット（設定は保持）
happy --reset --keep-config

# クリーンな再起動
pkill -f happy && rm -rf ~/.happy/cache && happy

# 強制的な再認証
claude auth logout && claude auth login && happy --regenerate-keys

# デバッグモードで起動
DEBUG=* happy --verbose
```

---

**Last Updated**: 2026-02-11
