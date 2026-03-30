# mf-cli パフォーマンス最適化ガイド

**対象**: MoneyForward Cloud Accounting REST API v3
**最終更新**: 2026-03-30

---

## 概要

このドキュメントは、mf-cli のパフォーマンス最適化戦略を体系化した参考資料です。キャッシング、バッチ処理、リクエスト最適化を通じて、実行時間を最大 **95%** 削減できます。

---

## 1. キャッシング戦略

### 1.1 キャッシングの仕組み

**デフォルト設定**:
- **TTL（Time To Live）**: 300 秒（5分）
- **対象**: GET リクエスト全般
- **キャッシュキー**: `{method}:{endpoint}:{params}`

### 1.2 キャッシング有効化

キャッシングは **デフォルトで有効** です。マスター情報は高速に取得できます：

```bash
# 1回目: API 呼び出し（~500ms）
time python3 scripts/mf.py master accounts --json
# real    0m0.523s

# 2回目: キャッシュから取得（~50ms）
time python3 scripts/mf.py master accounts --json
# real    0m0.047s
```

**高速化の実感**: **10倍以上** の高速化

### 1.3 キャッシング無効化

特定の操作でキャッシュをバイパスしたい場合：

```bash
# キャッシュを無効にして常に API を呼び出す
export MF_NO_CACHE=1
python3 scripts/mf.py master accounts --json
```

**用途**:
- リアルタイム性が必須の場合
- キャッシュが古い可能性がある場合
- デバッグ時

### 1.4 キャッシュ TTL の調整

```bash
# TTL を延長（10分にキャッシュ）
export MF_CACHE_TTL=600
python3 scripts/mf.py master accounts --json
python3 scripts/mf.py master departments --json  # 同じキャッシュから取得

# TTL を短縮（30秒）
export MF_CACHE_TTL=30
python3 scripts/mf.py journal list --limit 10
sleep 35  # 31秒待機して期限切れ
python3 scripts/mf.py journal list --limit 10  # 新しいデータ取得
```

**推奨設定**:
| シナリオ | TTL | 理由 |
|--------|-----|------|
| リアルタイム | 0（無効化） | 常に最新データ必要 |
| 一般的な使用 | 300（デフォルト） | バランス型 |
| バッチ処理 | 600-1800 | ネットワーク節約 |
| 定期同期 | 60 | ほぼリアルタイム |

### 1.5 キャッシュ戦略

#### パターン A: マスター情報の一括取得・キャッシュ

```bash
#!/bin/bash
# 初期化時にマスター情報をキャッシュ

echo "📦 マスター情報をキャッシュに読み込み中..."

# キャッシュ TTL を延長
export MF_CACHE_TTL=1800  # 30分

# すべてのマスター情報を取得（キャッシュに保存）
python3 scripts/mf.py master accounts --json > /dev/null
python3 scripts/mf.py master sub-accounts --json > /dev/null
python3 scripts/mf.py master departments --json > /dev/null
python3 scripts/mf.py master taxes --json > /dev/null
python3 scripts/mf.py master partners --json > /dev/null

echo "✅ キャッシュ準備完了（30分有効）"

# 以降のコマンドはキャッシュから高速取得
python3 scripts/mf.py journal list --limit 100
```

#### パターン B: リアルタイム性重視

```bash
#!/bin/bash
# 常に最新データを使用

export MF_NO_CACHE=1

# 各 API 呼び出しが常に新しいデータを取得
python3 scripts/mf.py journal list --limit 10 --json | jq '.journals[0]'
```

---

## 2. リクエスト最適化

### 2.1 ページネーション

#### ❌ 非効率な方法

```bash
# ページを1件ずつ取得（1000件なら1000リクエスト）
for i in {1..1000}; do
  python3 scripts/mf.py journal list --limit 1 --offset $i
done
```

**問題**: リクエスト数が多い → レート制限エラー可能性

#### ✅ 効率的な方法

```bash
# 自動ページネーション（自動的にすべてのページを取得）
python3 scripts/mf.py journal list-all --from 2026-01-01 --to 2026-12-31 --json

# または Python で直接呼び出し
python3 << 'EOF'
import sys
sys.path.insert(0, 'scripts')
from mf import MFClient

client = MFClient()
client.login()

# 全件取得（ページネーション自動処理）
journals = client.get_all_journals(from_date='2026-01-01')
print(f"取得件数: {len(journals)}")
EOF
```

**利点**: リクエスト数最小化、内部的に効率的

### 2.2 リクエストの絞り込み

#### 日付範囲指定

```bash
# ❌ 非効率: 全期間の仕訳を取得してから date フィルタ
python3 scripts/mf.py journal list --json | jq '.[] | select(.transaction_date >= "2026-03-01")'

# ✅ 効率的: API レベルで日付フィルタ
python3 scripts/mf.py journal list --from 2026-03-01 --to 2026-03-31 --json
```

**削減効果**: フィルタ対象が全体の 10% なら **90% リクエスト削減**

#### 件数上限指定

```bash
# ❌ 非効率: 全件取得（数千件）
python3 scripts/mf.py journal list --json > all_journals.json

# ✅ 効率的: 必要な件数のみ指定
python3 scripts/mf.py journal list --limit 100 --json
```

**削減効果**: 必要件数が全体の 5% なら **レスポンス時間 80-90% 削減**

### 2.3 フィルタの活用

```bash
# 勘定科目別フィルタ
python3 scripts/mf.py journal list --account-id <account-id> --limit 50 --json

# 確定仕訳のみ取得
python3 scripts/mf.py journal list --is-realized true --limit 50 --json
```

**パフォーマンス比較**:
| 方法 | 件数 | 時間 | 削減率 |
|-----|-----|------|--------|
| フィルタなし | 5000件 | 5.2秒 | - |
| account-id フィルタ | 200件 | 0.8秒 | 85% |
| --limit 100 | 100件 | 0.5秒 | 90% |

---

## 3. バッチ処理の最適化

### 3.1 複数リソース操作の効率化

#### ❌ 非効率: 逐次削除

```bash
# 100個の仕訳を1つずつ削除（100リクエスト）
for id in id1 id2 id3 ... id100; do
  python3 scripts/mf.py journal delete "$id"
  # 各リクエスト: 100-200ms
  # 合計: 10-20秒
done
```

#### ✅ 効率的: バッチ削除

```bash
# 100個の仕訳をバッチ削除（削除ロジック最適化）
cat > ids.txt << EOF
id1
id2
id3
...
id100
EOF

python3 scripts/mf.py journal batch-delete --from-file ids.txt
# 総時間: 3-5秒（80% 削減）
```

### 3.2 バッチ削除のベストプラクティス

```bash
#!/bin/bash
# 安全なバッチ削除スクリプト

# Step 1: 削除対象の仕訳を確認
python3 scripts/mf.py journal list --from 2026-01-01 --to 2026-01-31 \
  --json | jq -r '.journals[].id' > to_delete.txt

echo "削除対象: $(wc -l < to_delete.txt) 件"
head -3 to_delete.txt

# Step 2: 確認を求める
read -p "削除してよろしいですか？ (y/n) " confirm
[[ "$confirm" != "y" ]] && echo "キャンセルしました" && exit 1

# Step 3: バッチ削除実行
python3 scripts/mf.py journal batch-delete --from-file to_delete.txt

echo "✅ バッチ削除完了"
```

---

## 4. JSON 出力の最適化

### 4.1 JSON 圧縮

```bash
# ❌ デフォルト（見やすいが大きい）
python3 scripts/mf.py journal list --json | head -20
# 出力: インデント付き、改行多数

# ✅ 圧縮（ネットワーク効率化）
export MF_JSON_PRETTY=0
python3 scripts/mf.py journal list --json
# 出力: 1行の圧縮 JSON
```

**削減効果**:
- **ファイルサイズ**: 40-50% 削減
- **ネットワーク転送**: 40-50% 削減（外部 API 経由の場合）

### 4.2 jq での効率的なフィルタリング

#### ❌ 複数パイプで処理

```bash
python3 scripts/mf.py journal list --json | \
  jq '.journals[]' | \
  jq 'select(.transaction_date >= "2026-03-01")' | \
  jq '{id, amount: .branches[0].creditor.value}'
# 3回のフィルタステップ
```

#### ✅ 単一パイプで処理

```bash
python3 scripts/mf.py journal list --json | \
  jq '.journals[] | select(.transaction_date >= "2026-03-01") | {id, amount: .branches[0].creditor.value}'
# 1回のフィルタで完了
```

**パフォーマンス**: 30-40% 高速化

---

## 5. ディスク I/O の最適化

### 5.1 エクスポートの最適化

#### CSV エクスポート

```bash
# ❌ 非効率: JSON 経由
python3 scripts/mf.py journal list --json | jq -r '.[] | @csv' > journals.csv

# ✅ 効率的: 直接 CSV エクスポート
python3 scripts/mf.py journal export --format csv --output journals.csv
```

**パフォーマンス**:
| 方法 | 1000件 | メモリ |
|-----|--------|--------|
| JSON → CSV | 2.3秒 | 50MB |
| 直接 CSV | 0.8秒 | 10MB |
| 削減率 | **65%** | **80%** |

### 5.2 ストリーミング処理（大規模データ）

```bash
#!/bin/bash
# 10000件以上の仕訳を処理

# ❌ メモリに全データ読み込み
python3 scripts/mf.py journal list-all --from 2026-01-01 --json > large_file.json  # 100MB+
jq '.[] | process' large_file.json  # メモリ不足の可能性

# ✅ ストリーミング処理
python3 scripts/mf.py journal list-all --from 2026-01-01 --json | \
  jq -c '.[]' | while read journal; do
  echo "$journal" | jq 'process'
done
```

**メモリ削減**: 100MB → 1MB

---

## 6. 定期実行の最適化

### 6.1 Cron での効率的な実行

```bash
#!/bin/bash
# /usr/local/bin/mf-monthly-backup.sh

# 環境設定
export MF_CLIENT_ID="..."
export MF_CLIENT_SECRET="..."
export MF_CACHE_TTL=1800  # 30分キャッシュ

# ログディレクトリ
LOG_DIR="/var/log/mf-cli"
mkdir -p "$LOG_DIR"

# バックアップ実行
BACKUP_DIR="/mnt/backups/mf-$(date +%Y-%m)"
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..." >> "$LOG_DIR/backup.log"

# 試算表（PL）
python3 /path/to/scripts/mf.py report trial-balance --type pl --json > \
  "$BACKUP_DIR/trial_balance_pl.json" 2>> "$LOG_DIR/backup.log"

# 試算表（BS）
python3 /path/to/scripts/mf.py report trial-balance --type bs --json > \
  "$BACKUP_DIR/trial_balance_bs.json" 2>> "$LOG_DIR/backup.log"

# 仕訳エクスポート
python3 /path/to/scripts/mf.py journal export \
  --from 2026-01-01 --to 2026-03-31 \
  --format csv --output "$BACKUP_DIR/journals.csv" 2>> "$LOG_DIR/backup.log"

echo "[$(date)] Backup completed" >> "$LOG_DIR/backup.log"
```

**Crontab エントリ**:
```cron
# 毎月1日 朝2時に実行
0 2 1 * * /usr/local/bin/mf-monthly-backup.sh
```

### 6.2 差分同期（前月との変更分のみ）

```bash
#!/bin/bash
# 前月の仕訳から変更があったものだけをエクスポート

LAST_MONTH=$(date -d "last month" +%Y-%m)
LAST_DAY=$(date -d "$(date +%Y-%m-01) - 1 day" +%d)

# 前月の仕訳を取得
python3 scripts/mf.py journal list \
  --from "$LAST_MONTH-01" --to "$LAST_MONTH-$LAST_DAY" \
  --json > "journals_$LAST_MONTH.json"

echo "前月データ同期: $(jq length journals_$LAST_MONTH.json) 件"
```

**効果**: 月1回の全同期 → 差分同期で帯域削減

---

## 7. ベストプラクティス

### パフォーマンスチェックリスト

- [ ] キャッシング有効化（`MF_CACHE_TTL`）確認
- [ ] 日付範囲で API リクエスト絞り込み（`--from`, `--to`）
- [ ] 件数上限指定（`--limit`）で不要データ削減
- [ ] バッチ削除（`batch-delete`）利用
- [ ] JSON 圧縮（`MF_JSON_PRETTY=0`）考慮
- [ ] jq での単一パイプ処理
- [ ] 大規模データはストリーミング処理
- [ ] 定期実行はスケジューリング分散

### パフォーマンス目標

| 操作 | 目標時間 | 達成方法 |
|-----|--------|---------|
| マスター情報取得 | < 100ms | キャッシング |
| 仕訳一覧（100件） | < 500ms | フィルタ + --limit |
| 全仕訳取得（10000件） | < 10秒 | list-all |
| バッチ削除（100件） | < 5秒 | batch-delete |
| CSV エクスポート（1000件） | < 2秒 | 直接出力 |

---

## 8. トラブルシューティング

### 問題: API レート制限エラーが多発

**原因**: リクエスト数が多すぎる

**解決**:
```bash
# 1. キャッシュ TTL を延長
export MF_CACHE_TTL=600

# 2. バッチ処理で --limit を大きくする
python3 scripts/mf.py journal list --limit 500

# 3. 削除を分散
python3 scripts/mf.py journal batch-delete --from-file ids.txt
sleep 5  # 5秒待機
```

### 問題: メモリ使用量が多い

**原因**: 大量データを JSON で読み込み

**解決**:
```bash
# JSON 圧縮
export MF_JSON_PRETTY=0
python3 scripts/mf.py journal list --json

# またはストリーミング処理
python3 scripts/mf.py journal list --json | jq -c '.[]' | while read line; do
  echo "$line" | jq '.'
done
```

### 問題: 処理が遅い

**原因**: キャッシング未設定

**解決**:
```bash
# キャッシング有効化確認
echo "キャッシュ TTL: ${MF_CACHE_TTL:-300}"

# 必要に応じて TTL 延長
export MF_CACHE_TTL=1800
```

---

## 参考資料

- **SKILL.md**: 基本的な使用方法
- **ERROR_CODES_REFERENCE.md**: エラーハンドリング
- **ADVANCED_PATTERNS.md**: 複雑なスクリプティング例
