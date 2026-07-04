---
name: claude-skill-manager
description: Create, test, improve, publish, and manage Claude Code Agent Skills. Use when creating new skills, modifying existing skills, running skill evaluations, optimizing descriptions, publishing to GitHub, or managing skill repositories. Also use when users mention skill creation, SKILL.md, skill testing, or skill publishing.
version: 1.0.0
author: asgr-base
createDate: 2026-03-02
updateDate: 2026-03-02
license: Apache-2.0
disable-model-invocation: true
---

# Claude Skill Manager

スキルのライフサイクル全体を管理する統合スキル。Anthropic公式skill-creatorをベースに、設計原則とリポジトリ管理を統合。

## ツールパス

Anthropic公式 [skill-creator](https://github.com/anthropics/skills) をローカルにクローンし、そのパスを `$SKILL_CREATOR` として参照する。

```bash
# セットアップ（初回のみ）
git clone https://github.com/anthropics/skills.git <任意のパス>/anthropics-skills
SKILL_CREATOR=<任意のパス>/anthropics-skills/skills/skill-creator
```

## ワークフロー概要

```
1. Intent Capture（意図把握）
2. Interview & Research（ヒアリング・調査）
3. SKILL.md作成
4. テストケース作成・評価実行
5. フィードバック収集・改善ループ
6. Description最適化
7. リポジトリへ公開
```

ユーザーがどの段階にいるかを判断して、そこから支援を開始する。

---

## Phase 1: スキル作成

### 1.1 Intent Capture

会話の文脈からまず以下を把握:

1. スキルで何を実現したいか
2. どんなユーザー入力でトリガーされるべきか
3. 期待する出力フォーマット
4. テストケースを作成すべきか（客観的に検証可能な出力 → Yes、主観的な出力 → ユーザーに確認）

既存の会話からワークフローをキャプチャする場合（「これをスキルにして」）、使用したツール、手順、修正内容を会話履歴から抽出。

### 1.2 Interview & Research

テストケース作成前に以下を確認:
- エッジケース、入出力フォーマット、サンプルファイル
- 成功基準、依存関係
- 利用可能なMCPがあれば活用して調査

### 1.3 SKILL.md作成

#### スキル構造

```
skill-name/
├── SKILL.md              # 必須（500行未満）
├── references/           # 詳細ドキュメント（必要時に読み込み）
├── scripts/              # ユーティリティスクリプト
└── assets/               # テンプレート、アイコン等
```

#### Progressive Disclosure（3レベル読み込み）

| Level | タイミング | コスト | 内容 |
|-------|-----------|--------|------|
| L1 | 常に | ~100語 | name + description |
| L2 | トリガー時 | <500行 | SKILL.md本文 |
| L3 | 必要時 | 無制限 | references/, scripts/ |

#### YAMLフロントマター

**必須**: `name`（小文字・数字・ハイフン、64文字以内）, `description`（1,024文字以内）
**オプション**: `license`, `allowed-tools`, `metadata`
**注意**: `version`, `author`等はパッケージ化時にエラーになる。ローカル用途のみ。

#### descriptionの書き方

- 三人称で記述（システムプロンプトに注入されるため）
- 機能 + 使用タイミングを含める
- **やや"pushy"に**（undertrigger防止）: 具体的なキーワード・文脈を列挙

```yaml
# Good
description: Extract text from PDF files using Docling. Use when working with PDFs, document extraction, table extraction, or converting documents to Markdown.

# Bad
description: I can help you process PDF files
```

#### 執筆スタイル

- 命令形で指示を書く
- **WHYを説明する**（ALWAYS/NEVER多用より効果的）
- 具体例を含める
- 一般化して特定例に過学習しない

### 1.4 初期化スクリプト（オプション）

```bash
python $SKILL_CREATOR/scripts/init_skill.py my-new-skill --path ~/.claude/skills
```

PyYAML依存。macOS Homebrew環境では: `cd /tmp && python3 -m venv skill-env && source skill-env/bin/activate && pip install pyyaml`
スクリプト実行時: `source /tmp/skill-env/bin/activate` してから実行。

---

## Phase 2: テスト・評価

### 2.1 テストケース作成

2-3個の現実的なテストプロンプトを作成し、ユーザーに確認。`evals/evals.json`に保存:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {"id": 1, "prompt": "User's task prompt", "expected_output": "Description of expected result", "files": []}
  ]
}
```

### 2.2 評価実行

結果は `<skill-name>-workspace/iteration-N/` に保存。

**各テストケースに対して2つのサブエージェントを同時起動**:

| 実行 | 説明 | 保存先 |
|------|------|--------|
| **with-skill** | スキルありで実行 | `eval-ID/with_skill/outputs/` |
| **baseline** | スキルなし or 旧版で実行 | `eval-ID/without_skill/outputs/` |

### 2.3 実行中にアサーション作成

実行完了を待たず、定量的アサーションをドラフト。客観的に検証可能なもののみ。

### 2.4 タイミングデータ保存

サブエージェント完了通知から `total_tokens`, `duration_ms` を `timing.json` に保存（この機会を逃すとデータ消失）。

### 2.5 グレーディング・集約・ビューアー

1. **グレーディング**: `$SKILL_CREATOR/agents/grader.md` を読み、各アサーションを評価
2. **集約**:
   ```bash
   cd $SKILL_CREATOR && python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
3. **分析**: `$SKILL_CREATOR/agents/analyzer.md` を参照してパターン分析
4. **ビューアー起動**:
   ```bash
   python $SKILL_CREATOR/eval-viewer/generate_review.py <workspace>/iteration-N --skill-name "my-skill" --benchmark <workspace>/iteration-N/benchmark.json
   ```
   iteration 2+ では `--previous-workspace` も指定。

IMPORTANT: 自分で評価を始める**前に**、必ずビューアーを生成してユーザーに提示すること。

### 2.6 フィードバック読み込み・改善

`feedback.json` を読み込み:
- 空フィードバック = 問題なし
- 具体的な指摘があるケースに集中改善

改善の原則:
- フィードバックから**一般化**する（過学習しない）
- 効果のない指示は削除
- WHYを説明する
- テストケース間で繰り返されるヘルパースクリプトはバンドル

改善後、新しい `iteration-N+1/` で再評価 → ユーザーが満足するまで繰り返し。

---

## Phase 3: Description最適化

### 3.1 トリガー評価クエリ生成

20個のクエリを生成（should-trigger 8-10 + should-not-trigger 8-10）。

- **現実的で具体的**なクエリ（ファイルパス、会社名、状況説明を含む）
- should-not-triggerは**紛らわしいもの**（明らかに無関係なものは無意味）

### 3.2 ユーザーレビュー

`$SKILL_CREATOR/assets/eval_review.html` テンプレートを使用してHTMLを生成、ブラウザで表示。

### 3.3 最適化ループ実行

```bash
cd $SKILL_CREATOR && python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <current-model-id> \
  --max-iterations 5 --verbose
```

60% train / 40% test分割、各クエリ3回実行で信頼性確保。

### 3.4 結果適用

`best_description` でSKILL.mdを更新。Before/Afterとスコアをユーザーに報告。

---

## Phase 4: バリデーション・パッケージ化

```bash
# バリデーション
python $SKILL_CREATOR/scripts/quick_validate.py <path-to-skill>

# パッケージ化（配布用）
python $SKILL_CREATOR/scripts/package_skill.py <path-to-skill> ./dist
```

### チェックリスト

- [ ] `name`: 小文字・ハイフン・数字のみ、64文字以内
- [ ] `description`: 機能+トリガー条件、1,024文字以内、三人称
- [ ] SKILL.md本文: 500行未満
- [ ] 詳細情報は references/ に分離
- [ ] ファイル参照が1レベルの深さ

---

## Phase 5: リポジトリ管理・公開

スキルをGitリポジトリで管理し、シンボリックリンクで `~/.claude/skills/` に配置するパターン。

### 推奨ローカル構成

```
$VAULT/
├── .claude/skills/
│   └── my-skill ↵ → repos/$ORG/skills-repo/skills/my-skill
└── repos/$ORG/
    ├── skills-public/         # 公開スキル（GitHub public repo）
    ├── skills-private/        # 非公開スキル（GitHub private repo）
    └── anthropics-skills/     # Anthropic公式（参照用、git clone）
```

`$VAULT` = Claude Code作業ディレクトリ、`$ORG` = GitHub組織名またはユーザー名。

### 公開/非公開の判断

| 公開リポジトリ | 非公開リポジトリ |
|---------------|----------------|
| 汎用的なスキル | 個人固有のワークフロー |
| 機密情報なし | API キー、パスワード含む |
| 他者に有用 | 個人情報含む |

### 公開手順

```bash
# 1. リポジトリ最新化
cd <skills-repo> && git pull

# 2. スキルをコピー
cp -r ~/.claude/skills/SKILL_NAME ./skills/

# 3. 機密情報チェック（ローカルパス、APIキー、個人名等を除去）

# 4. シンボリックリンク作成（実体をリポジトリ側に置き換え）
rm -rf ~/.claude/skills/SKILL_NAME
ln -sf $(pwd)/skills/SKILL_NAME ~/.claude/skills/SKILL_NAME

# 5. コミット＆プッシュ
git add skills/SKILL_NAME && git commit -m "Add SKILL_NAME skill" && git push
```

### 新規PCセットアップ

```bash
# 1. スキルリポジトリをクローン
mkdir -p $VAULT/repos && cd $VAULT/repos
gh repo clone $ORG/skills-public
gh repo clone $ORG/skills-private    # 非公開（認証必要）
git clone https://github.com/anthropics/skills.git anthropics-skills

# 2. シンボリックリンク作成（必要なスキルを選択）
for skill in skill-a skill-b; do
  ln -sf $VAULT/repos/$ORG/skills-public/skills/$skill ~/.claude/skills/$skill
done
```

---

## 参照ファイル

### skill-creator（公式）

| ファイル | 用途 |
|----------|------|
| `$SKILL_CREATOR/agents/grader.md` | アサーション評価指示 |
| `$SKILL_CREATOR/agents/comparator.md` | ブラインドA/B比較 |
| `$SKILL_CREATOR/agents/analyzer.md` | ベンチマーク分析 |
| `$SKILL_CREATOR/references/schemas.md` | JSON構造定義 |

### 設計原則（詳細）

| ファイル | 用途 |
|----------|------|
| [DESIGN-PRINCIPLES.md](DESIGN-PRINCIPLES.md) | Progressive Disclosure、ワークフロー、パターン集 |

### 外部リソース

- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [anthropics/skills](https://github.com/anthropics/skills)
