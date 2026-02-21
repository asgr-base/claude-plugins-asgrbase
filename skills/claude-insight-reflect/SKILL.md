---
name: claude-insight-reflect
description: Claude Code Insightレポートを日本語翻訳し、示唆をCLAUDE.mdに反映。/insights、使用状況分析、改善提案関連の質問時に使用。
version: 2.4.0
---

# Claude Insight Reflect

Claude Codeの `/insights` レポートを生成・翻訳・分析し、示唆をプロジェクト設定に反映するスキル。

## `/insights` レポートの生成方法

> **`/insights` はビルトインスラッシュコマンドだが、以下のコマンドでBashから生成可能:**
>
> ```bash
> CLAUDECODE= claude -p "/insights" 2>&1
> ```
>
> - `CLAUDECODE` 環境変数をunsetしてネストセッション制限を回避
> - `-p` (print mode) で非対話的に実行
> - 生成先: `~/.claude/usage-data/report.html`（上書き）
> - 所要時間: 約30-60秒
>
> **注意**: Skill toolで `/insights` を呼び出すことはできない（ビルトインコマンドは対象外）。Bashから上記コマンドを実行すること。

## クイックリファレンス

| タスク | コマンド |
|--------|----------|
| レポート生成・翻訳・反映（フル） | `/claude-insight-reflect` |
| レポート生成のみ | `/claude-insight-reflect --generate-only` |
| レポート翻訳のみ | `/claude-insight-reflect --translate-only` |
| 示唆反映のみ（翻訳済みレポートから） | `/claude-insight-reflect --apply-only` |

## 前提条件

1. **出力ディレクトリ**: `.claude/usage-data/` が存在すること
2. **Claude CLI**: `claude` コマンドがPATH上で利用可能であること

## レポートファイルの場所

| ファイル | 場所 | 説明 |
|----------|------|------|
| 最新レポート（ソース） | `~/.claude/usage-data/report.html` | `/insights` が生成する場所（上書き） |
| 日付アーカイブ | `.claude/usage-data/report-YYYYMMDD.html` | プロジェクト配下にコピーした保存版 |
| 日本語翻訳版 | `.claude/usage-data/report-YYYYMMDD-ja.html` | 翻訳後のファイル |

## ワークフロー

### Step 0: レポートの生成

当日のレポートが存在しない場合、自動的に生成する。

**判定フロー**:
1. プロジェクト配下 `.claude/usage-data/report-YYYYMMDD.html` が存在する → Step 1 へスキップ
2. `~/.claude/usage-data/report.html` が当日更新済み → Step 1 へスキップ
3. いずれでもない → 以下のコマンドで生成:

```bash
CLAUDECODE= claude -p "/insights" 2>&1
```

- タイムアウト: 120秒を設定
- 生成完了後、`~/.claude/usage-data/report.html` の更新日時を確認して成功を検証
- 生成に失敗した場合、ユーザーに通知して終了: 「レポート生成に失敗しました。手動で `/insights` を実行してください。」

### Step 1: レポートの特定とアーカイブ

- プロジェクト配下 `.claude/usage-data/` に当日の `report-YYYYMMDD.html` があるか確認
- なければ `~/.claude/usage-data/report.html` をコピー: `cp ~/.claude/usage-data/report.html .claude/usage-data/report-$(date +%Y%m%d).html`

### Step 2: レポートの日本語翻訳（Bash/Python一括翻訳）

> **IMPORTANT: サブエージェントでの翻訳・Edit toolでの大量置換は禁止**
>
> - サブエージェント一括翻訳 → コンテキスト制限超過で完了しない
> - `run_in_background: true` サブエージェント → Write toolが自動拒否される
> - 複数サブエージェント並列 → 同一ファイル競合エラー
> - メインコンテキストでEdit tool大量呼び出し → ユーザー承認疲れ
>
> **すべての翻訳をBash + Python heredocで実行すること。**

**翻訳方式: 3段階方式（コピー → 翻訳マップ生成 → Bash/Python一括置換）**

#### Stage 1: HTMLコピー

```bash
cp .claude/usage-data/report-YYYYMMDD.html .claude/usage-data/report-YYYYMMDD-ja.html
```

#### Stage 2: 翻訳マップの生成（サブエージェント）

**Task tool（`subagent_type: general-purpose`）でHTMLを読み込み、包括的な翻訳マップを作成**:

- サブエージェントにHTMLファイル全文を読ませる（Read only、編集なし）
- 以下のカテゴリ別に英語→日本語の対応表を生成させる:
  - A. HTML属性（lang, title）
  - B. ナビゲーション/TOCリンク
  - C. セクション見出し（h1, h2, h3）
  - D. 統計ラベル（Messages, Lines等）
  - E. チャートタイトル・バーラベル（全チャート）
  - F. ボタンラベル・JS文字列・タイムゾーン・ヘルパーテキスト
  - G. ナラティブ段落（At a Glance, How You Use CC等）
  - H. Feature Cards（タイトル、説明、おすすめ理由）
  - I. Pattern Cards（タイトル、要約、詳細）
  - J. Horizon Cards（タイトル、説明、始め方）
  - K. Fun ending（見出し、本文）
  - L. CLAUDE.md推奨項目（cmd-code, cmd-why の表示テキスト）

このステップの出力は翻訳マップのみ（ファイル編集なし）。

#### Stage 3: Bash/Pythonスクリプトで一括置換

翻訳マップをもとに、**Bash toolからPython heredocスクリプトを実行**:

```bash
python3 << 'PYEOF'
filepath = '.claude/usage-data/report-YYYYMMDD-ja.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()
count = 0
replacements = [
    ('>English text<', '>日本語テキスト<'),
    # ... 置換ペアのリスト ...
]
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        count += 1
    else:
        print(f"  WARNING: not found: {old[:60]}...")
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Replacements: {count}. File saved.")
PYEOF
```

**スクリプト分割の目安**（実績: 192件/9スクリプト）:

| スクリプト | 対象カテゴリ | 置換数目安 |
|-----------|------------|:--------:|
| 1 | UI要素（A〜F: 属性・ナビ・見出し・統計・チャート・ボタン・JS） | 80-100 |
| 2 | At a Glance（G） | 10-15 |
| 3 | How You Use CC（G） | 7-10 |
| 4 | プロジェクトエリア（G） + How You Use CC残り | 15-20 |
| 5 | Big Wins + Friction（G） | 15-20 |
| 6 | Feature Cards（H） | 8-12 |
| 7 | Pattern Cards（I） | 8-10 |
| 8 | Horizon Cards（J） | 8-12 |
| 9 | Fun ending + CLAUDE.md推奨項目（K, L） | 12-16 |

**各スクリプト実行後に置換数を確認**し、WARNINGが出た場合はテキストの正確な一致を検証して修正。

**翻訳対象外（英語のまま保持）**:
- CSS・JavaScriptのロジック
- `<code class="example-code">` 内のコード例（スキル設定、シェルコマンド等）
- `<code class="copyable-prompt">` 内のコピー可能プロンプト（Claude Codeに貼り付ける用途）
- `data-text` 属性（クリップボードペイロード）
- チャートのツール名バーラベル（Bash, Read, Edit, TodoWrite等）
- チャートの言語名バーラベル（Markdown, HTML, Python等）
- 時間範囲ラベル（2-10s, 10-30s等の数値ラベル）
- 技術用語（Claude Code, MCP, CLAUDE.md, Docling, openpyxl, Feedly等）
- URL・href属性

**出力**: `.claude/usage-data/report-YYYYMMDD-ja.html`

### Step 3: 示唆の分析

日本語レポートから以下のセクションを抽出・分析:

| セクション | 分析ポイント |
|------------|--------------|
| **At a Glance** | うまくいっていること / 障害になっていること / すぐできる改善 |
| **試すべき機能** | 未使用のClaude Code機能で有用なもの |
| **カスタムスキル** | スキルの改善提案 |
| **セッション分析** | 非効率なパターンの特定 |
| **エラー分析** | 頻出エラーと対策 |
| **CLAUDE.md推奨事項** | レポートが提示するコピー可能なルール |

### Step 4: CLAUDE.mdへの反映

分析結果に基づき、以下を更新:

```markdown
## HOW（必須ルール）

### [新規セクション名]

[示唆から導出されたルール・ガイドライン]
```

**反映基準**:
- 繰り返し発生する問題 → 必須ルールとして追加
- 効率化の提案 → ベストプラクティスとして追加
- スキル固有の改善 → 該当スキルのSKILL.mdに追加
- レポートの「Copy」ボタン付き推奨事項 → そのまま反映を検討

### Step 5: スキルへの反映

示唆が特定のスキルに関連する場合:

1. 該当スキルの `SKILL.md` を特定
2. 「チェックリスト」セクションに追加
3. ワークフローの改善点を反映

## 自動反映チェックリスト

Claude Codeが示唆反映時に必ず確認するステップ:

1. **レポート全体の確認**
   - 「At a Glance」セクションで全体像を把握
   - 「試すべき機能」セクションを確認
   - 「カスタムスキル」セクションを確認
   - 「セッション分析」で非効率パターンを特定
   - 「CLAUDE.md推奨事項」のコピー可能なルールを確認

2. **反映先の判断**
   - 汎用ルール → CLAUDE.md
   - スキル固有 → 該当SKILL.md
   - 新規スキル提案 → ユーザーに確認

3. **重複チェック**
   - 既存のルールと重複しないか確認
   - 類似ルールがあれば統合を検討

4. **ユーザー確認**
   - 反映する示唆をリスト表示
   - 「すべて追加」「選択して追加」「スキップ」を選択肢として提示

## 出力ファイル

| ファイル | 説明 |
|----------|------|
| `.claude/usage-data/report-YYYYMMDD.html` | 英語版レポート（アーカイブ） |
| `.claude/usage-data/report-YYYYMMDD-ja.html` | 日本語版レポート |
| `CLAUDE.md` | 更新されたプロジェクト設定 |
| `*.SKILL.md` | 更新されたスキル設定（該当する場合） |

## エラーハンドリング

| 状況 | 対処 |
|------|------|
| レポートが見つからない | Step 0 で自動生成を試行。失敗時はユーザーに手動 `/insights` 実行を案内 |
| レポート生成タイムアウト | 120秒以内に完了しない場合、ユーザーに手動実行を案内 |
| 翻訳対象ファイルなし | `.claude/usage-data/` 内のHTMLファイルを確認 |
| CLAUDE.md更新失敗 | ファイルパスと権限を確認 |

## 禁止事項

- **Bashで `claude insights` を実行しない** — 正しくは `CLAUDECODE= claude -p "/insights"`
- **Skill toolで `/insights` を呼び出さない** — ビルトインコマンドはSkill tool対象外
- **サブエージェントでHTML翻訳（Read→Edit/Write）を実行しない** — コンテキスト制限超過、Write tool自動拒否、並列競合で失敗する。サブエージェントは翻訳マップ生成（Read only）にのみ使用
- **Edit toolで大量の翻訳置換を実行しない** — 承認要求が多すぎてユーザー体験を損なう。すべての置換はBash + Python heredocで実行
- **複数サブエージェントで同一ファイルを並列編集しない** — 「File has been modified since read」エラーで失敗する

## 注意事項

- **手動確認推奨**: 示唆の反映前にユーザーに確認を求める
- **バックアップ**: CLAUDE.md更新前に変更内容を表示
- **増分更新**: 既存のルールを上書きせず、追加・統合する
- **Last Updated更新**: CLAUDE.md更新時は日付を更新

---

**Version**: 2.4.0
**Last Updated**: 2026-02-20
