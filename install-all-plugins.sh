#!/bin/bash

# asgr-base Claude Plugins - 全24プラグインインストールスクリプト
# 使用方法: このスクリプトの内容をClaude Codeターミナルにコピー&ペーストして実行

echo "🚀 asgr-base マーケットプレイス - 全24プラグインインストール開始"
echo ""
echo "注意: 以下のコマンドをClaude Codeのターミナルで実行してください"
echo "=================================================="
echo ""

# 24個のプラグインリスト
PLUGINS=(
  "aml-cft-guide"
  "atlassian-manager"
  "claude-code-guide"
  "claude-insight-reflect"
  "claude-md-guide"
  "claude-mem-guide"
  "claude-rename"
  "claude-sessions-sync"
  "claude-skill-manager"
  "feedly-intelligence-report"
  "happy-mobile-client"
  "jp-aoiro-accounting"
  "jp-eltax-guide"
  "jp-etax-guide"
  "jp-law-verification"
  "jp-legal-amendment-pdf2md"
  "m365-ai-bridge-manager"
  "moneyforward-manager"
  "openclaw-guide"
  "pdf2md-docling"
  "pre-publish-audit"
  "skill-scanner"
  "tailscale-guide"
  "yayoi-aoiro-guide"
)

# インストールコマンド生成
count=0
for plugin in "${PLUGINS[@]}"; do
  count=$((count + 1))
  echo "/plugin install $plugin@asgr-base"
done

echo ""
echo "=================================================="
echo "合計 $count 個のプラグインをインストールします"
echo ""
echo "全インストール後、以下で確認:"
echo "  /plugin list"
echo ""
echo "プラグイン削除は:"
echo "  /plugin uninstall <プラグイン名>@asgr-base"
