# mf-cli 高度な使用パターン

**対象**: MoneyForward Cloud Accounting REST API v3
**最終更新**: 2026-03-30

---

## 概要

このドキュメントは、mf-cli を使った高度なスクリプティングパターンと運用ケースを体系化した参考資料です。

---

## 1. Python スクリプティング

### 1.1 基本的な利用パターン

```python
#!/usr/bin/env python3
"""mf-cli を Python から直接利用するパターン"""

import sys
sys.path.insert(0, '/path/to/scripts')
from mf import MFClient

# クライアント初期化
client = MFClient()
client.login()

# 事業者情報取得
office_info = client.get_office()
print(f"事業者: {office_info.get('name')}")

# 仕訳一覧取得
journals = client.list_journals(limit=50)
print(f"仕訳数: {len(journals.get('journals', []))}")

# 勘定科目取得
accounts = client.get_accounts()
print(f"勘定科目数: {len(accounts)}")
```

### 1.2 エラーハンドリング

```python
#!/usr/bin/env python3
"""エラーハンドリングの実装例"""

import sys
sys.path.insert(0, 'scripts')
from mf import MFClient

def safe_journal_delete(journal_id, retry_count=3):
    """仕訳削除（エラー対応）"""
    client = MFClient()
    client.login()

    for attempt in range(retry_count):
        try:
            result = client.delete_journal(journal_id)
            print(f"✅ 削除成功: {journal_id}")
            return True
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                print(f"❌ 仕訳が見つかりません: {journal_id}")
                return False
            elif "429" in error_msg:
                print(f"⚠️ レート制限（{attempt+1}/{retry_count}）")
                import time
                time.sleep(2 ** attempt)  # 指数バックオフ
            else:
                print(f"❌ エラー: {error_msg}")
                return False

    return False

# 使用例
if __name__ == "__main__":
    success = safe_journal_delete("journal_id_123")
    sys.exit(0 if success else 1)
```

### 1.3 バッチ処理の実装

```python
#!/usr/bin/env python3
"""複数仕訳の効率的な処理"""

import sys
sys.path.insert(0, 'scripts')
from mf import MFClient
from datetime import datetime, timedelta

def process_journals_by_account(account_id, days_back=30):
    """特定勘定科目の過去N日間の仕訳を処理"""

    client = MFClient()
    client.login()

    # 日付範囲計算
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=days_back)

    # フィルタ付き取得
    journals = client.list_journals(
        account_id=account_id,
        from_date=str(from_date),
        to_date=str(to_date)
    )

    print(f"📊 勘定科目 {account_id}")
    print(f"   期間: {from_date} ～ {to_date}")
    print(f"   件数: {len(journals.get('journals', []))}")

    # 集計処理
    total_debit = 0
    total_credit = 0

    for journal in journals.get('journals', []):
        for branch in journal.get('branches', []):
            debitor = branch.get('debitor', {})
            creditor = branch.get('creditor', {})

            total_debit += debitor.get('value', 0)
            total_credit += creditor.get('value', 0)

    print(f"   合計借方: {total_debit:,}円")
    print(f"   合計貸方: {total_credit:,}円")

    return {
        'account_id': account_id,
        'period': f"{from_date} - {to_date}",
        'count': len(journals.get('journals', [])),
        'total_debit': total_debit,
        'total_credit': total_credit
    }

if __name__ == "__main__":
    result = process_journals_by_account("account_123", days_back=30)
    print(f"\n✅ 処理完了: {result}")
```

### 1.4 マスター情報の同期

```python
#!/usr/bin/env python3
"""マスター情報をキャッシュに同期"""

import sys
sys.path.insert(0, 'scripts')
from mf import MFClient
import json
from pathlib import Path

def sync_master_data():
    """全マスター情報を取得・キャッシュに保存"""

    client = MFClient()
    client.login()

    cache_dir = Path.home() / '.mf-cli' / 'master_cache'
    cache_dir.mkdir(parents=True, exist_ok=True)

    print("📦 マスター情報の同期開始...")

    masters = {
        'accounts': client.get_accounts(),
        'sub_accounts': client.get_sub_accounts(),
        'departments': client.get_departments(),
        'taxes': client.get_taxes(),
        'partners': client.get_partners(),
        'connected_accounts': client.get_connected_accounts()
    }

    for name, data in masters.items():
        cache_file = cache_dir / f"{name}.json"

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        count = len(data) if isinstance(data, list) else len(data.get('data', []))
        print(f"  ✅ {name}: {count} 件")

    print(f"✅ キャッシュディレクトリ: {cache_dir}")

if __name__ == "__main__":
    sync_master_data()
```

---

## 2. 高度な CLI パターン

### 2.1 複雑な jq フィルタリング

```bash
#!/bin/bash
# 複数条件での仕訳フィルタリング

# 条件:
# 1. 2026年3月以降
# 2. 金額 1000円以上
# 3. 勘定科目が売上

python3 scripts/mf.py journal list --json | jq '
  .journals[] |
  select(.transaction_date >= "2026-03-01") |
  select((.branches[0].creditor.value + .branches[0].creditor.tax_value) >= 1000) |
  select(.branches[0].account_id == "sales_account_id") |
  {
    id: .id,
    date: .transaction_date,
    amount: (.branches[0].creditor.value + .branches[0].creditor.tax_value),
    description: .description
  }
'
```

### 2.2 月別集計

```bash
#!/bin/bash
# 月別の売上集計

python3 scripts/mf.py journal list --json | jq -r '
  .journals[] |
  select(.branches[0].account_id == "sales_account_id") |
  {
    month: .transaction_date[0:7],
    amount: (.branches[0].creditor.value + .branches[0].creditor.tax_value)
  }
' | jq -s 'group_by(.month) | map({
  month: .[0].month,
  total: map(.amount) | add
})'
```

**出力例**:
```json
[
  { "month": "2026-01", "total": 1500000 },
  { "month": "2026-02", "total": 1200000 },
  { "month": "2026-03", "total": 1800000 }
]
```

### 2.3 CSV への変換・Excel 連携

```bash
#!/bin/bash
# 仕訳を CSV にエクスポートして Excel で開く

python3 scripts/mf.py journal export \
  --from 2026-01-01 --to 2026-03-31 \
  --format csv --output quarterly_journals.csv

# macOS で Excel で開く
open -a "Microsoft Excel" quarterly_journals.csv

# Linux の場合
# libreoffice --calc quarterly_journals.csv

# Windows PowerShell の場合
# Start-Process -FilePath "quarterly_journals.csv"
```

### 2.4 Slack への自動通知

```bash
#!/bin/bash
# 日次仕訳登録通知を Slack に送信

WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
TODAY=$(date +%Y-%m-%d)

# 本日の仕訳数
JOURNAL_COUNT=$(python3 scripts/mf.py journal list --from "$TODAY" --to "$TODAY" --json | jq '.journals | length')

# Slack メッセージ作成
MESSAGE=$(cat <<EOF
{
  "text": "📊 本日の仕訳登録通知",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*本日の仕訳登録*\n登録件数: $JOURNAL_COUNT 件"
      }
    }
  ]
}
EOF
)

# Slack に送信
curl -X POST -H 'Content-type: application/json' \
  --data "$MESSAGE" \
  "$WEBHOOK_URL"

echo "✅ Slack 通知送信: $JOURNAL_COUNT 件"
```

---

## 3. 運用自動化パターン

### 3.1 毎月末の自動バックアップ

```bash
#!/bin/bash
# /usr/local/bin/mf-monthly-backup.sh

# 毎月末に以下を実行:
# 1. 試算表（PL、BS）をバックアップ
# 2. 仕訳をエクスポート
# 3. バックアップをクラウド同期

BACKUP_ROOT="/mnt/mf-backups"
CURRENT_MONTH=$(date +%Y-%m)
BACKUP_DIR="$BACKUP_ROOT/$CURRENT_MONTH"

mkdir -p "$BACKUP_DIR"

echo "🔄 $(date) - 月次バックアップ開始"

# 試算表（PL）
python3 /path/to/scripts/mf.py report trial-balance \
  --type pl --json > "$BACKUP_DIR/trial_balance_pl.json"
echo "  ✅ 試算表（PL）"

# 試算表（BS）
python3 /path/to/scripts/mf.py report trial-balance \
  --type bs --json > "$BACKUP_DIR/trial_balance_bs.json"
echo "  ✅ 試算表（BS）"

# 仕訳エクスポート
python3 /path/to/scripts/mf.py journal export \
  --from "${CURRENT_MONTH}-01" \
  --format csv --output "$BACKUP_DIR/journals.csv"
echo "  ✅ 仕訳エクスポート"

# Google Drive に同期（gog-cli 使用）
gog drive upload "$BACKUP_DIR" --parent "FOLDER_ID" \
  --recurse --overwrite
echo "  ✅ Google Drive 同期"

echo "✅ $(date) - バックアップ完了"
```

**Crontab エントリ**:
```cron
# 毎月末 23時に実行
0 23 28-31 * * [ $(date +\%d -d tomorrow) == 01 ] && /usr/local/bin/mf-monthly-backup.sh
```

### 3.2 週次試算表レポート

```bash
#!/bin/bash
# 毎週月曜日に試算表をメール送信

REPORT_DATE=$(date +%Y-%m-%d)
REPORT_FILE="/tmp/trial_balance_$REPORT_DATE.json"

# 試算表（PL）取得
python3 scripts/mf.py report trial-balance --type pl --json > "$REPORT_FILE"

# メール送信（sendmail または mail コマンド）
cat "$REPORT_FILE" | mail -s "試算表レポート $REPORT_DATE" user@example.com

echo "✅ 試算表をメール送信: $REPORT_DATE"
```

**Crontab エントリ**:
```cron
# 毎週月曜日 8時に実行
0 8 * * 1 /usr/local/bin/mf-weekly-report.sh
```

### 3.3 定期同期（会計ソフト他システムとの連携）

```bash
#!/bin/bash
# 外部システムとの差分同期

SYNC_DIR="/var/mf-sync"
LAST_SYNC_FILE="$SYNC_DIR/.last_sync"

# 前回同期日を取得（初回は昨日）
if [ -f "$LAST_SYNC_FILE" ]; then
  LAST_SYNC=$(cat "$LAST_SYNC_FILE")
else
  LAST_SYNC=$(date -d "yesterday" +%Y-%m-%d)
fi

CURRENT_DATE=$(date +%Y-%m-%d)

echo "📡 差分同期: $LAST_SYNC ～ $CURRENT_DATE"

# 差分データをエクスポート
python3 scripts/mf.py journal export \
  --from "$LAST_SYNC" --to "$CURRENT_DATE" \
  --format json --output "$SYNC_DIR/delta_journals.json"

# 外部システムに POST
curl -X POST \
  -H "Content-Type: application/json" \
  -d @"$SYNC_DIR/delta_journals.json" \
  https://external-system.example.com/api/journals/sync

# 同期日を更新
echo "$CURRENT_DATE" > "$LAST_SYNC_FILE"

echo "✅ 差分同期完了"
```

---

## 4. トラブルシューティング・デバッグパターン

### 4.1 詳細ログ出力

```bash
#!/bin/bash
# デバッグモードで詳細ログ出力

export MF_CLI_DEBUG=1
export MF_CLI_VERBOSE=1

python3 scripts/mf.py journal list --limit 5 --json 2>&1 | tee debug.log

echo "ログファイル: debug.log"
```

### 4.2 API レスポンス検査

```bash
#!/bin/bash
# API レスポンスの詳細検査

# JSON 構造の確認
python3 scripts/mf.py journal list --limit 1 --json | jq 'keys'

# 特定フィールドの確認
python3 scripts/mf.py journal list --limit 1 --json | \
  jq '.journals[0] | keys'

# null 値の確認
python3 scripts/mf.py journal list --limit 10 --json | \
  jq '.journals[] | map_values(select(. == null)) | select(length > 0)'
```

### 4.3 パフォーマンスプロファイリング

```bash
#!/bin/bash
# 各操作のパフォーマンス測定

echo "⏱️ パフォーマンス測定"

# マスター情報取得
echo "勘定科目取得:"
time python3 scripts/mf.py master accounts --json > /dev/null

# 仕訳一覧（キャッシュなし）
echo "仕訳一覧（キャッシュなし）:"
export MF_NO_CACHE=1
time python3 scripts/mf.py journal list --limit 100 --json > /dev/null

# 仕訳一覧（キャッシュ有）
echo "仕訳一覧（キャッシュ有）:"
unset MF_NO_CACHE
time python3 scripts/mf.py journal list --limit 100 --json > /dev/null

# 試算表取得
echo "試算表取得:"
time python3 scripts/mf.py report trial-balance --type pl --json > /dev/null
```

---

## 5. スクリプト例：会計データ分析

### 5.1 勘定科目別の月別売上集計

```python
#!/usr/bin/env python3
"""勘定科目別の月別売上集計"""

import sys
sys.path.insert(0, 'scripts')
from mf import MFClient
from collections import defaultdict
from datetime import datetime

def monthly_sales_summary(year):
    """指定年度の勘定科目別月別売上集計"""

    client = MFClient()
    client.login()

    # 全仕訳を取得
    from_date = f"{year}-01-01"
    to_date = f"{year}-12-31"
    journals = client.get_all_journals(from_date=from_date, to_date=to_date)

    # 勘定科目別に集計
    summary = defaultdict(lambda: defaultdict(float))

    for journal in journals:
        month = journal['transaction_date'][:7]  # YYYY-MM

        for branch in journal.get('branches', []):
            account_id = branch.get('account_id')
            creditor = branch.get('creditor', {})
            amount = creditor.get('value', 0) + creditor.get('tax_value', 0)

            summary[account_id][month] += amount

    # テーブル出力
    print(f"\n📊 {year}年度 勘定科目別月別売上集計")
    print("=" * 120)

    # ヘッダー
    months = [f"{year}-{m:02d}" for m in range(1, 13)]
    header = "勘定科目".ljust(20) + " | " + " | ".join(months)
    print(header)
    print("-" * 120)

    # データ行
    for account_id, monthly_data in sorted(summary.items()):
        row = account_id.ljust(20) + " | "
        values = [f"{monthly_data[m]:>10,.0f}" for m in months]
        row += " | ".join(values)
        print(row)

    print("=" * 120)

if __name__ == "__main__":
    monthly_sales_summary(2026)
```

### 5.2 期間比較分析

```python
#!/usr/bin/env python3
"""前期比較分析"""

import sys
sys.path.insert(0, 'scripts')
from mf import MFClient

def compare_periods(period1_from, period1_to, period2_from, period2_to):
    """2期間の比較分析"""

    client = MFClient()
    client.login()

    # 各期間のデータ取得
    journals1 = client.get_all_journals(from_date=period1_from, to_date=period1_to)
    journals2 = client.get_all_journals(from_date=period2_from, to_date=period2_to)

    # 金額集計
    total1 = sum(b['creditor']['value']
                 for j in journals1
                 for b in j.get('branches', []))

    total2 = sum(b['creditor']['value']
                 for j in journals2
                 for b in j.get('branches', []))

    # 分析結果
    growth_rate = ((total2 - total1) / total1 * 100) if total1 > 0 else 0

    print(f"\n📊 期間比較分析")
    print(f"期間1 ({period1_from} ~ {period1_to}): {total1:,}円 ({len(journals1)}件)")
    print(f"期間2 ({period2_from} ~ {period2_to}): {total2:,}円 ({len(journals2)}件)")
    print(f"成長率: {growth_rate:+.1f}%")

    if growth_rate > 10:
        print("✅ 成長傾向")
    elif growth_rate < -10:
        print("⚠️ 減少傾向")
    else:
        print("➡️ 横ばい")

if __name__ == "__main__":
    compare_periods('2026-01-01', '2026-03-31', '2026-04-01', '2026-06-30')
```

---

## 参考資料

- **SKILL.md**: 基本的な使用方法
- **ERROR_CODES_REFERENCE.md**: エラーハンドリング
- **PERFORMANCE_OPTIMIZATION.md**: パフォーマンス最適化
- **Python API ドキュメント**: `scripts/mf.py` の docstring 参照
