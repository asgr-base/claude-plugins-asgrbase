# 設定ファイル仕様

このドキュメントは `~/.feedly/config.json` の仕様を定義します。

## ファイル配置

```
~/.feedly/
├── token          # APIトークン（必須）
├── browser_data/  # ブラウザデータ（トークン自動取得用）
└── config.json    # 設定ファイル（必須）
```

**重要**: 設定ファイルはスキル外（`~/.feedly/`）に配置。スキル本体には個人設定を含めない。

## 設定スキーマ

```json
{
  "token_file": "~/.feedly/token",
  "output_dir": "Daily",
  "fetch_count": 1000,
  "time_range_hours": null,
  "unread_only": true,

  "global_keywords": ["AI", "eKYC", "本人確認"],

  "synonym_groups": [
    ["AI", "人工知能", "機械学習", "LLM"]
  ],

  "scoring": {
    "weights": {
      "engagement": 0.30,
      "relevance": 0.40,
      "freshness": 0.20,
      "source_trust": 0.10
    },
    "thresholds": {
      "must_read": 55,
      "should_read": 45,
      "optional": 35
    }
  },

  "trusted_sources": {
    "example.com": 1.0
  },

  "paywalled_domains": [
    "bunshun.jp",
    "nikkei.com"
  ],

  "categories": [
    {
      "name": "Feedlyのカテゴリ名",
      "slug": "category-slug",
      "keywords": ["カテゴリ固有キーワード"],
      "trusted_sources": {
        "category-specific.com": 1.0
      }
    }
  ],

  "deduplication": {
    "title_similarity_threshold": 0.7,
    "content_similarity_threshold": 0.8,
    "time_window_hours": 48
  },

  "report": {
    "max_articles_per_category": 20,
    "include_summary": true,
    "include_related": true,
    "language": "ja"
  }
}
```

## フィールド説明

### 基本設定

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `token_file` | string | Yes | トークンファイルパス |
| `output_dir` | string | Yes | レポート出力先（プロジェクトルートからの相対パス） |
| `fetch_count` | int | No | 取得記事数上限（デフォルト: 1000） |
| `time_range_hours` | int/null | No | 取得対象期間（null=無制限、デフォルト: null） |
| `unread_only` | bool | No | 未読記事のみ取得（デフォルト: true） |

### global_keywords

全カテゴリ共通の関連度判定用キーワード。記事タイトル・本文にこれらのキーワードが含まれると関連度スコアが上がる。

### synonym_groups

同義語グループ。同一グループ内のキーワードは同等に扱われる。例えば「AI」と「人工知能」は同じトピックとして判定。

### scoring

| フィールド | 説明 |
|-----------|------|
| `weights.engagement` | 注目度の重み（0-1） |
| `weights.relevance` | キーワード関連度の重み（0-1） |
| `weights.freshness` | 鮮度の重み（0-1） |
| `weights.source_trust` | ソース信頼度の重み（0-1） |
| `thresholds.must_read` | MUST READの閾値（0-100） |
| `thresholds.should_read` | SHOULD READの閾値（0-100） |
| `thresholds.optional` | OPTIONALの閾値（0-100） |

### trusted_sources

グローバルなソース信頼度設定。ドメイン名をキー、信頼度（0-1）を値として設定。

### paywalled_domains

有料記事（ペイウォール付き）のドメインリスト。該当ドメインの記事はスコアに関係なく「PAYWALLED」カテゴリに分類される。

```json
"paywalled_domains": [
  "bunshun.jp",
  "nikkei.com"
]
```

### categories[]

カテゴリ別の設定。**`stream_id`は不要**（global.allから自動取得）。

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `name` | string | Yes | **Feedly側のカテゴリ名と完全一致** |
| `slug` | string | Yes | ファイル名用識別子（英数字・ハイフン） |
| `keywords` | string[] | No | カテゴリ固有の関連度判定用キーワード |
| `trusted_sources` | object | No | カテゴリ固有のソース信頼度（0-1） |

**重要**: `name`はFeedlyで設定したカテゴリ名と完全に一致させる必要があります。一致しない場合、Feedlyのカテゴリ名がそのままslugとして使用されます。

### deduplication

| フィールド | 説明 |
|-----------|------|
| `title_similarity_threshold` | タイトル類似度の閾値（0-1） |
| `content_similarity_threshold` | 本文類似度の閾値（0-1） |
| `time_window_hours` | 重複検出の時間窓 |

## カテゴリ名の確認方法

Feedlyで設定したカテゴリ名を確認するには:

```bash
curl -s -H "Authorization: Bearer $(cat ~/.feedly/token)" \
     "https://api.feedly.com/v3/categories" | jq '.[].label'
```

## 設定例のパターン

### 仕事重視

```json
"weights": {
  "engagement": 0.20,
  "relevance": 0.50,
  "freshness": 0.20,
  "source_trust": 0.10
}
```

### 速報重視

```json
"weights": {
  "engagement": 0.40,
  "relevance": 0.20,
  "freshness": 0.30,
  "source_trust": 0.10
}
```

### 未読管理なし（全記事取得）

```json
"unread_only": false,
"time_range_hours": 24
```

---

**Last Updated**: 2026-02-04
