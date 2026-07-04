#!/bin/bash

# Happy - Claude Code Mobile Client Status Checker
# このスクリプトはHappyの稼働状況を確認します

echo "========================================="
echo "Happy Mobile Client - Status Check"
echo "========================================="
echo ""

# カラー定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Node.jsとnpmのチェック
echo "1. Node.js & npm"
echo "-------------------"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js installed: $NODE_VERSION"
else
    echo -e "${RED}✗${NC} Node.js not found"
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓${NC} npm installed: $NPM_VERSION"
else
    echo -e "${RED}✗${NC} npm not found"
fi
echo ""

# 2. happy-coderのインストール確認
echo "2. happy-coder Installation"
echo "-------------------"
if command -v happy &> /dev/null; then
    HAPPY_VERSION=$(npm list -g happy-coder 2>/dev/null | grep happy-coder | awk '{print $2}')
    if [ -z "$HAPPY_VERSION" ]; then
        echo -e "${YELLOW}⚠${NC} happy command found but version unclear"
    else
        echo -e "${GREEN}✓${NC} happy-coder installed: $HAPPY_VERSION"
    fi
else
    echo -e "${RED}✗${NC} happy-coder not installed"
    echo -e "${YELLOW}→${NC} Install with: npm install -g happy-coder"
fi
echo ""

# 3. Claude Codeの認証状態確認
echo "3. Claude Code Authentication"
echo "-------------------"
if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>/dev/null | head -n 1)
    echo -e "${GREEN}✓${NC} Claude CLI installed: $CLAUDE_VERSION"

    # 認証状態を確認（エラー出力を抑制）
    AUTH_CHECK=$(claude auth status 2>&1)
    if echo "$AUTH_CHECK" | grep -q "Authenticated\|logged in"; then
        echo -e "${GREEN}✓${NC} Claude authenticated"
    elif echo "$AUTH_CHECK" | grep -q "Not authenticated\|not logged in"; then
        echo -e "${RED}✗${NC} Claude not authenticated"
        echo -e "${YELLOW}→${NC} Run: claude auth login"
    else
        echo -e "${YELLOW}⚠${NC} Authentication status unclear"
    fi
else
    echo -e "${RED}✗${NC} Claude CLI not found"
fi
echo ""

# 4. 実行中のHappyプロセス確認
echo "4. Running Happy Processes"
echo "-------------------"
HAPPY_PROCESSES=$(ps aux | grep -i "[h]appy" | grep -v grep)
if [ -z "$HAPPY_PROCESSES" ]; then
    echo -e "${YELLOW}⚠${NC} No Happy processes running"
else
    echo -e "${GREEN}✓${NC} Happy processes found:"
    echo "$HAPPY_PROCESSES" | awk '{print "  PID: "$2", Command: "$11" "$12" "$13}'
fi
echo ""

# 5. ネットワーク接続確認
echo "5. Network Connectivity"
echo "-------------------"
if ping -c 1 google.com &> /dev/null; then
    echo -e "${GREEN}✓${NC} Internet connection active"
else
    echo -e "${RED}✗${NC} No internet connection"
fi
echo ""

# 6. ポート使用状況確認（Happyが使用する可能性のあるポート）
echo "6. Port Usage"
echo "-------------------"
HAPPY_PORTS=$(lsof -i -P 2>/dev/null | grep -i happy)
if [ -z "$HAPPY_PORTS" ]; then
    echo -e "${YELLOW}⚠${NC} No Happy-related ports detected"
else
    echo -e "${GREEN}✓${NC} Happy ports in use:"
    echo "$HAPPY_PORTS"
fi
echo ""

# 7. システムリソース確認
echo "7. System Resources"
echo "-------------------"
if command -v free &> /dev/null; then
    # Linux
    FREE_MEM=$(free -h | grep Mem | awk '{print $4}')
    echo "Available Memory: $FREE_MEM"
elif command -v vm_stat &> /dev/null; then
    # macOS
    FREE_PAGES=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    if [ ! -z "$FREE_PAGES" ]; then
        FREE_MB=$((FREE_PAGES * 4096 / 1024 / 1024))
        echo "Available Memory: ~${FREE_MB}MB"
    fi
fi

CPU_USAGE=$(top -l 1 | grep "CPU usage" 2>/dev/null || echo "CPU info unavailable")
echo "$CPU_USAGE"
echo ""

# サマリー
echo "========================================="
echo "Summary"
echo "========================================="

ISSUES=0

# 必須コンポーネントのチェック
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗${NC} Node.js is required"
    ((ISSUES++))
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗${NC} npm is required"
    ((ISSUES++))
fi

if ! command -v happy &> /dev/null; then
    echo -e "${RED}✗${NC} happy-coder is not installed"
    ((ISSUES++))
fi

if ! command -v claude &> /dev/null; then
    echo -e "${RED}✗${NC} Claude CLI is not installed"
    ((ISSUES++))
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All required components are ready"
    echo ""
    echo "To start Happy, run:"
    echo "  cd /path/to/your/project"
    echo "  happy"
else
    echo -e "${YELLOW}⚠${NC} Found $ISSUES issue(s) - see details above"
fi

echo ""
echo "========================================="
echo "For troubleshooting, see:"
echo "  .claude/skills/happy-mobile-client/TROUBLESHOOTING.md"
echo "========================================="
