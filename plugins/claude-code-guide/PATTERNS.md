# Claude Code ベストプラクティスパターン

## 基盤構築パターン

### Two-Instance Kickoffパターン

新しいリポジトリを開始する際、2つのClaudeインスタンスを使用:

**Instance 1: Scaffolding Agent**
- スキャフォールドと基盤を構築
- プロジェクト構造を作成
- 設定をセットアップ（CLAUDE.md、rules、agents）
- 規約を確立
- スケルトンを配置

**Instance 2: Deep Research Agent**
- 全サービス、Web検索などに接続
- 詳細なPRDを作成
- アーキテクチャMermaidダイアグラムを作成
- 実際のドキュメントからのクリップを含むリファレンスをコンパイル

```
┌─────────────────────────────┬─────────────────────────────┐
│       Left Terminal         │       Right Terminal        │
│                             │                             │
│    Scaffolding Agent        │    Deep Research Agent      │
│    /rename ecc-code         │    /rename ecc-qs           │
│                             │                             │
│    - Project structure      │    - PRD creation           │
│    - Config files           │    - Architecture diagrams  │
│    - Conventions            │    - Documentation refs     │
└─────────────────────────────┴─────────────────────────────┘
```

### llms.txtパターン

多くのドキュメントサイトでLLM最適化版が利用可能:

```
https://www.example.com/docs/llms.txt
```

クリーンなLLM最適化版ドキュメントを直接Claudeに入力可能。

---

## コンテキスト管理パターン

### Strategic Compactパターン

自動コンパクトを無効化し、論理的な区切りで手動実行:

```
[探索フェーズ]
     │
     ▼
  /compact ◄── 探索後、実行前
     │
     ▼
[実装フェーズ]
     │
     ▼
  /compact ◄── マイルストーン完了後
     │
     ▼
[次のマイルストーン]
```

**コンパクトすべきタイミング**:
- 探索から実装への移行時
- メジャーマイルストーン完了後
- コンテキストが不要な情報で肥大化した時

### Memory Persistenceパターン

```
SESSION 1                       SESSION 2
─────────                       ─────────
   │                               │
   ▼                               ▼
┌─────────────┐              ┌─────────────┐
│ SessionStart│◄── nothing   │ SessionStart│◄── loads
│    Hook     │              │    Hook     │    context
└──────┬──────┘              └──────┬──────┘
       │                            │
       ▼                            ▼
   [Working]                    [Working]
       │                        (informed)
       ▼                            │
┌─────────────┐                     ▼
│ PreCompact  │──► saves       [Continue]
│    Hook     │    state
└──────┬──────┘
       │
       ▼
   [Compacted]
       │
       ▼
┌─────────────┐
│    Stop     │──► persists to
│    Hook     │    sessions/
└─────────────┘
```

---

## サブエージェントパターン

### Iterative Retrievalパターン

サブエージェントの要約が不十分な場合の対処:

```
┌─────────────────┐
│  ORCHESTRATOR   │
│  (has context)  │
└────────┬────────┘
         │ query + objective
         ▼
┌─────────────────┐
│   SUB-AGENT     │
│ (lacks context) │
└────────┬────────┘
         │ summary
         ▼
┌─────────────────┐     ┌─────────────┐
│    EVALUATE     │─no─►│  FOLLOW-UP  │
│   Sufficient?   │     │  QUESTIONS  │
└────────┬────────┘     └──────┬──────┘
         │ yes                 │
         ▼                     │
     [ACCEPT]             sub-agent
         │                fetches
         ◄─────────────────────┘
           (max 3 cycles)
```

**実装ポイント**:
1. クエリだけでなく目的コンテキストも渡す
2. 全てのサブエージェント返却を評価
3. 受け入れ前にフォローアップ質問
4. 最大3サイクルで無限ループ防止

### Sequential Phasesパターン

```
Phase 1: RESEARCH
├── Agent: Explore
├── Input: Requirements
├── Output: research-summary.md
│
Phase 2: PLAN
├── Agent: planner
├── Input: research-summary.md
├── Output: plan.md
│
Phase 3: IMPLEMENT
├── Agent: tdd-guide
├── Input: plan.md
├── Output: Code changes
│
Phase 4: REVIEW
├── Agent: code-reviewer
├── Input: All changes
├── Output: review-comments.md
│
Phase 5: VERIFY
├── Agent: build-error-resolver
├── Input: Test results
└── Output: Done or loop back
```

**ルール**:
- 各エージェントに1入力、1出力
- 出力が次の入力
- フェーズをスキップしない
- エージェント間で`/clear`
- 中間出力をファイルに保存

---

## 並列化パターン

### Cascadeパターン

複数Claude Codeインスタンスの整理方法:

```
Tab 1        Tab 2        Tab 3        Tab 4
(oldest)                              (newest)
   │            │            │            │
   └────────────┴────────────┴────────────┘
                    ▼
            左から右へスイープ
            古いものから新しいものへ
```

**ルール**:
- 新タスクは右の新タブで開く
- 左から右へスイープ
- 最大3-4タスクに集中
- 特定タスクを必要に応じてチェック

### Fork vs Worktreeの使い分け

| 状況 | 推奨 |
|------|------|
| コード重複なし | /fork |
| コード重複あり | Git worktree |
| リサーチのみ | /fork |
| 複数機能実装 | Git worktree |

```bash
# 非重複タスク
# Terminal 1: /fork でリサーチ
# Terminal 2: メインでコード変更

# 重複タスク
git worktree add ../feature-a -b feature-a
git worktree add ../feature-b -b feature-b
# 各worktreeで別々のClaude
```

---

## 検証パターン

### Checkpoint-Based Evalパターン

線形ワークフロー向け:

```
[Task 1]
    │
    ▼
┌─────────────┐
│ Checkpoint 1│◄── 基準に対して検証
└──────┬──────┘
       │ pass?
   ┌───┴───┐
  yes     no──► fix ──┐
   │              │    │
   ▼              └────┘
[Task 2]
    │
    ▼
┌─────────────┐
│ Checkpoint 2│
└──────┬──────┘
       │
      ...
```

**適用場面**:
- 明確なマイルストーンがある機能実装
- 段階的な構築プロセス

### Continuous Evalパターン

長時間セッション/探索的リファクタリング向け:

```
    [Work]
       │
       ▼
  ┌─────────┐
  │ Timer/  │
  │ Change  │
  └────┬────┘
       │
       ▼
┌──────────────┐
│  Run Tests   │
│   + Lint     │
└──────┬───────┘
       │
  ┌────┴────┐
pass       fail
  │          │
  ▼          ▼
[Continue] [Stop & Fix]
               │
               └──► [Continue]
```

**適用場面**:
- 明確なマイルストーンがないリファクタリング
- 長時間の保守作業

---

## トークン最適化パターン

### Model Escalationパターン

```
         ┌─────────┐
         │  Task   │
         └────┬────┘
              │
              ▼
    ┌───────────────────┐
    │ Simple & Clear?   │
    └─────────┬─────────┘
              │
        ┌─────┴─────┐
       yes          no
        │            │
        ▼            ▼
    ┌───────┐   ┌────────────────┐
    │ Haiku │   │ Multiple files │
    └───────┘   │ or complex?    │
                └───────┬────────┘
                        │
                  ┌─────┴─────┐
                 no          yes
                  │            │
                  ▼            ▼
              ┌────────┐   ┌───────┐
              │ Sonnet │   │ Opus  │
              └────────┘   └───────┘
```

### Background Process Offloadパターン

```
# Claude内で実行（トークン消費）
> npm run build
[大量の出力がコンテキストを消費]

# Claude外で実行（トークン節約）
$ tmux new -s build
$ npm run build
# 必要な部分だけコピーしてClaudeに渡す
```

---

## 学習パターン

### Continuous Learningパターン

```
[Session Work]
      │
      ▼
┌─────────────────┐
│ Discover Pattern│
│ or Workaround   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Manual: /learn  │
│ Auto: Stop hook │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Pattern │
│ → New Skill     │
└────────┬────────┘
         │
         ▼
~/.claude/skills/learned/
```

### Session Reflectionパターン

```
[Session End]
      │
      ▼
┌─────────────────┐
│ Reflection Agent│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ Worked │ │ Failed │
└────┬───┘ └────┬───┘
     │          │
     └────┬─────┘
          │
          ▼
┌─────────────────┐
│ Update Memory   │
│ File            │
└─────────────────┘
          │
          ▼
[Next Session Loads]
```

---

## アンチパターン

### 避けるべきこと

| アンチパターン | 問題 | 代替案 |
|---------------|------|--------|
| 全MCP常時有効 | コンテキスト枯渇 | 10個以下に制限 |
| 任意の並列数 | 管理オーバーヘッド | 必要最小限 |
| コンパクトなし | 古いコンテキスト蓄積 | 戦略的コンパクト |
| 単一巨大ファイル | 読み込みトークン浪費 | モジュラー構造 |
| サブエージェント過信 | 情報欠落 | 反復的取得 |
| UserPromptSubmit多用 | レイテンシ増大 | Stopフック優先 |

### フェーズスキップの危険

```
# 悪い例
Research → [SKIP PLAN] → Implement
                            │
                            ▼
                    方向性の誤り、手戻り

# 良い例
Research → Plan → Review Plan → Implement
                      │
                      ▼
                 早期の方向修正
```

---

## 推奨ワークフロー

### 日常開発フロー

```
1. claude --system-prompt "$(cat ~/.claude/contexts/dev.md)"
2. /rename feature-xyz
3. タスクを開始
4. 必要に応じて /fork でリサーチ
5. 論理的な区切りで /compact
6. セッション終了時に状態をファイルに保存
```

### PRレビューフロー

```
1. claude --system-prompt "$(cat ~/.claude/contexts/review.md)"
2. gh pr checkout <PR番号>
3. 変更をレビュー
4. コメント/承認
```

### 大規模リファクタリングフロー

```
1. Git worktreeを作成
2. 各worktreeで別Claudeインスタンス
3. Continuous evalを有効化
4. カスケードパターンで管理
5. 定期的にマージ・コンフリクト解決
```

---

## クイックリファレンス

### 問題 → 解決策マッピング

| 問題 | 解決策 |
|------|--------|
| コンテキスト枯渇 | MCP削減、/compact、モジュラーコード |
| セッション間の記憶喪失 | Memory Persistenceフック |
| 同じ間違いを繰り返す | Continuous Learningスキル |
| 並列作業でコンフリクト | Git worktree |
| トークンコスト高 | Haiku活用、mgrep、tmux |
| サブエージェントの情報不足 | Iterative Retrieval |
| 方向性の誤り | Sequential Phases |

---

**Version**: 1.0.0
**Last Updated**: 2026-01-25
**Source**: @affaanmustafa's Shorthand/Longform Guides
