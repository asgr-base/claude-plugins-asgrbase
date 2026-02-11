---
name: feedly-intelligence-report
description: Feedlyから記事を取得し、重複統合・関連度スコアリング・注目度ランキングを行いインテリジェンスレポートを生成。Feedly、RSS、ニュースレポート、記事まとめ関連の質問時に使用。
---

# Feedly Intelligence Report

Feedlyの記事を分析し、カテゴリ別のインテリジェンスレポートを生成するスキル。

## クイックリファレンス

| タスク | コマンド |
|--------|----------|
| 全カテゴリレポート | `/feedly-intelligence-report` |
| 特定カテゴリ | `/feedly-intelligence-report <slug>` |
| **トークン更新** | `uv run --with playwright --with requests python scripts/feedly_token_refresh.py` |
| トークン有効性確認 | `uv run --with playwright --with requests python scripts/feedly_token_refresh.py --check` |
| セットアップ確認 | `uv run --with requests python scripts/feedly_fetch.py --test` |
| 記事を既読にする | `uv run --with requests python scripts/feedly_fetch.py --mark-read /tmp/feedly_articles.json` |
| Read Laterに保存 | `uv run --with requests python scripts/feedly_bookmark.py --report <report.md> --mapping /tmp/url_to_entry_id.json` |

## 自動レポート生成チェックリスト

Claude Codeがレポート生成時に必ず実行するステップ:

1. **ページネーションで全件取得**
   - `continuation`トークンを使用して結果がなくなるまで継続
   - 途中で止めない（250件制限に注意）

2. **誤検出除外でキーワードスコアリング**
   - 除外キーワード: `aim`, `zaim` など（部分一致で除外）
   - タイトルマッチは本文マッチの2倍の重み

3. **カテゴリとサマリー付きMarkdownレポート生成**
   - MUST READ / SHOULD READ / OPTIONAL / SKIP に分類
   - 各記事にスコア内訳を表示

4. **完了前の件数検証**
   - 「Feedlyの未読件数」と「取得した記事数」が一致することを確認
   - 不一致の場合は取得を継続し、一致するまでレポート生成しない

## 前提条件

1. **Feedly Developer Access Token**: [SETUP.md](SETUP.md)参照
2. **設定ファイル**: `~/.feedly/config.json` を作成（[CONFIG.md](CONFIG.md)参照）

**重要**: 個人設定（カテゴリ、キーワード等）はスキル外の `~/.feedly/` に配置。

## ワークフロー

### 1. 記事取得

```bash
python scripts/feedly_fetch.py --config ~/.feedly/config.json --output /tmp/feedly_articles.json
```

**出力**: JSON形式の記事リスト（engagement, engagementRate含む）

**IMPORTANT: ページネーション**
- Feedly APIはデフォルトで最大250件/リクエスト
- 未読記事が250件を超える場合、`continuation`トークンを使用して全件取得すること
- レポート生成前に「期待される記事数」と「取得した記事数」が一致することを確認
- 一致しない場合は取得を継続

### 2. 記事分析

取得した記事に対し以下を実行:

#### 重複・類似記事の統合
- タイトル類似度（Jaccard係数）で重複検出
- 同一ニュースの複数ソースをグループ化
- 代表記事を選定（engagementRate最高のもの）

#### スコアリング

| 指標 | 計算方法 | デフォルト重み |
|------|----------|----------------|
| 注目度 | `engagementRate` × 100 | 30% |
| 関連度 | カテゴリキーワードマッチ数 | 40% |
| 鮮度 | 24時間以内=100, 48時間=50, それ以上=25 | 20% |
| ソース信頼度 | 設定ファイルで定義 | 10% |

**総合スコア** = Σ(指標 × 重み)

#### ライン引き

| ライン | 条件 | 推奨アクション |
|--------|------|----------------|
| **MUST READ** | スコア ≥ 55 | 必読。詳細確認推奨 |
| **SHOULD READ** | 45 ≤ スコア < 55 | 時間があれば読む |
| **OPTIONAL** | 35 ≤ スコア < 45 | 興味があれば |
| **SKIP** | スコア < 35 | スキップ可 |
| **PAYWALLED** | `paywalled_domains`に該当 | 有料記事（スコア関係なく分離） |

### 3. レポート生成

出力先: `Daily/YYYY-MM/YYYY-MM-DD（曜日）_feeds-report.md`

```
Daily/
└── YYYY-MM/
    └── YYYY-MM-DD（曜日）_feeds-report.md
```

**例**: `Daily/2026-02/2026-02-03（火）_feeds-report.md`

### 4. レポートフォーマット

```markdown
---
createDate: YYYY-MM-DD
author:
  - claude_code
tags:
  - "#feedly"
  - "#intelligence-report"
---

# Feedly インテリジェンスレポート

**生成日**: YYYY-MM-DD HH:MM
**記事数**: X件（重複除去後）

## スコアリング基準

### 総合スコア

```
総合スコア = 注目度×30% + 関連度×40% + 鮮度×20% + 信頼度×10%
```

**ライン引き**: MUST READ≧55 / SHOULD READ≧45 / OPTIONAL≧35

### 注目度 (0-100)

| 指標 | 計算式 | 上限 |
|------|--------|------|
| Feedly | engagementRate × 5 | 50点 |
| はてブ | ブックマーク数 × 2 | 40点 |
| HN | points × 0.5 | 40点 |

```
注目度 = min(Feedly + はてブ + HN, 100)
```

### 関連度 (0-100)

- キーワードマッチで計算（タイトルマッチは2倍の重み）
- 1つ以上マッチ: 基礎点30 + マッチ率に応じて最大70点追加
- マッチなし: 0点

### 鮮度 (0-100)

| 経過時間 | スコア |
|----------|--------|
| 24時間以内 | 100 |
| 48時間以内 | 50 |
| 72時間以内 | 35 |
| それ以上 | 25 |

### 信頼度 (0-100)

- 設定ファイルで定義されたソース: 定義値 × 100
- 未定義のソース: 50

---

## MUST READ (X件)

| # | 記事 | スコア | 注目 | Feedly | はてブ | HN | 関連 | 鮮度 | マッチKW | 読了 | 保存 |
|---|------|--------|------|--------|--------|-----|------|------|----------|------|------|
| 1 | [記事タイトル](URL) | **68.4** | 80.1 | 0.1 | 32 | 369 | 48.3 | 100 | claude, ai | [ ] | [ ] |

## SHOULD READ (X件)

| # | 記事 | スコア | 注目 | Feedly | はてブ | HN | 関連 | 鮮度 | マッチKW | 読了 | 保存 |
|---|------|--------|------|--------|--------|-----|------|------|----------|------|------|
| 1 | [記事タイトル](URL) | **52.5** | 42.9 | 2.9 | 51 | 0 | 36.7 | 100 | ai | [ ] | [ ] |

## OPTIONAL (X件)

| # | 記事 | スコア | 注目 | Feedly | はてブ | HN | 関連 | 鮮度 | マッチKW | 読了 | 保存 |
|---|------|--------|------|--------|--------|-----|------|------|----------|------|------|
| 1 | [記事タイトル](URL) | **44.5** | 4.9 | 2.9 | 1 | 0 | 45.0 | 100 | ai | [ ] | [ ] |

## SKIP (X件)

| # | 記事 | スコア | 注目 | Feedly | はてブ | HN | 関連 | 鮮度 | マッチKW | 読了 | 保存 |
|---|------|--------|------|--------|--------|-----|------|------|----------|------|------|
| 1 | [記事タイトル](URL) | **34.8** | 65.9 | 25.9 | 196 | 0 | 0 | 50 |  | [ ] | [ ] |
```

### テーブル列の説明

| 列 | 説明 |
|-----|------|
| スコア | 総合スコア（太字表記） |
| 注目 | 注目度スコア（0-100） |
| Feedly | Feedly engagementRate |
| はてブ | はてなブックマーク数 |
| HN | Hacker News points |
| 関連 | キーワード関連度スコア（0-100） |
| 鮮度 | 鮮度スコア（24h以内=100, 48h=50, それ以上=25） |
| マッチKW | マッチしたキーワード |
| 読了 | 読了チェックボックス |
| 保存 | Read Later保存チェックボックス |

### 5. Recommendation選定（Claude Code実行）

スコアリングの結果とは別に、OPTIONAL/SKIPに分類された記事の中からClaude Codeが独自の視点で5件を選定する。

**候補ファイル**: スコアリング時に自動生成される `*_recommendation-candidates.json`

**選定手順**:
1. 候補JSONファイルを読む（タイトル・URL・本文スニペット・ソース名を含む）
2. ユーザーの登録キーワード・注目サイト・はてブ/HNスコアに**関係なく**、一般的な面白さ・新規性・意外性の観点で5件を選ぶ
3. レポートの統計セクションの**直前**に以下のフォーマットで追記する

```markdown
## Recommendation (5件)

スコアリング基準では埋もれたが、独自の視点で注目に値する記事をAIが選定。

| # | 記事 | 選定理由 | 読了 | 保存 |
|---|------|----------|------|------|
| 1 | [記事タイトル](URL) | 一言の選定理由 | [ ] | [ ] |
```

**選定基準**（キーワードマッチ・ソース信頼度・ソーシャル指標は使わない）:
- 技術的に新しいアプローチや発見がある
- 意外な視点や異分野からの知見がある
- 将来のトレンドを先取りしている
- ニッチだが深い洞察がある
- 読み物として単純に面白い

### 6. Read Later保存（オプション）

レポートの「保存」列にチェックを入れた記事をFeedlyのRead Laterに保存できます。

**ワークフロー**:
1. レポート生成後、Obsidianで「保存」列にチェック `[x]` を入れる
2. 以下のコマンドを実行

```bash
python scripts/feedly_bookmark.py \
  --report Daily/2026-02/2026-02-03（火）_feeds-report.md \
  --mapping /tmp/url_to_entry_id.json
```

**オプション**:
- `--dry-run`: 実際に保存せず、対象記事を確認
- `--config`: 設定ファイルパス（デフォルト: `~/.feedly/config.json`）

**注意**: マッピングファイル（`url_to_entry_id.json`）は `feedly_fetch.py` 実行時に自動生成されます。

### 7. 既読確認（ユーザー確認必須）

レポート生成後、**必ずユーザーに確認**してから既読処理を行う。

```
YOU MUST: レポート生成後、以下の質問をユーザーに表示:

「レポートを生成しました。取得した{N}件の記事をFeedlyで既読にしますか？」

- 選択肢1: はい、既読にする
- 選択肢2: いいえ、未読のまま
```

ユーザーが「はい」を選択した場合のみ実行:

```bash
python scripts/feedly_fetch.py --mark-read /tmp/feedly_articles.json
```

**注意**:
- 既読にするのは取得したJSONファイル内の記事のみ
- 一度既読にすると元に戻せない
- レポートに含まれなかった記事（SKIPカテゴリ）も既読になる

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| トークン期限切れ | [SETUP.md](SETUP.md)の手順で再取得 |
| API制限超過 | 翌日まで待つ |
| カテゴリ未設定 | `~/.feedly/config.json` を確認 |
| 設定ファイルなし | [CONFIG.md](CONFIG.md)を参照して作成 |
| 既読マーク失敗 | トークン権限を確認（readとwriteの両方が必要） |

## 重複回避

デフォルトで**未読記事のみ**を取得します。レポート生成後に「既読にする」を選択すれば、次回のレポートには含まれません。

**動作**:
1. 記事取得時: Feedly APIの`unreadOnly=true`で未読記事のみ取得
2. レポート生成後: ユーザー確認を経て既読マーク
3. 次回取得時: 既読記事は自動的に除外

**設定**:
- `~/.feedly/config.json` に `"unread_only": false` を追加すると既読記事も含める
- コマンドライン: `--include-read` オプションで一時的に既読を含める

## 注意事項

- **APIリクエスト制限**: 月間100,000リクエストまで（無料プラン）
- **トークン有効期限**: 3ヶ月（自動延長なし）。Web Access Tokenは1週間程度
- **engagement未取得**: 一部記事はengagement情報なし（0として扱う）
- **URL取得**: はてブ等の集約サイト経由の場合、`canonicalUrl`がnullになることがある。その場合は`alternate[0].href`または`originId`から元記事URLを取得

## 詳細リファレンス

| ファイル | 内容 |
|----------|------|
| [SETUP.md](SETUP.md) | APIトークン取得・環境構築 |
| [CONFIG.md](CONFIG.md) | 設定ファイル仕様 |
| [scripts/feedly_token_refresh.py](scripts/feedly_token_refresh.py) | トークン自動取得スクリプト |
| [scripts/feedly_fetch.py](scripts/feedly_fetch.py) | Feedly API操作スクリプト |
| [scripts/feedly_score.py](scripts/feedly_score.py) | 記事スコアリング・レポート生成 |
| [scripts/feedly_bookmark.py](scripts/feedly_bookmark.py) | Read Later保存スクリプト |
| [config-sample.json](config-sample.json) | 設定ファイルのサンプル |

---

**Version**: 1.9.1
**Last Updated**: 2026-02-05
