# スキル設計原則 詳細リファレンス

## Progressive Disclosure

### 3レベル読み込みシステム

| Level | タイミング | コスト | 内容 |
|-------|-----------|--------|------|
| L1 | 起動時（全スキル） | ~100トークン/スキル | name + description |
| L2 | トリガー時 | <5,000トークン推奨 | SKILL.md本文 |
| L3+ | 必要時のみ | 無制限 | references/, scripts/ |

### パターン

#### 1. 高レベルガイド + 参照

```markdown
# PDF Processing

## Quick start
[基本操作]

## Advanced features
**Form filling**: See [FORMS.md](FORMS.md)
**API reference**: See [REFERENCE.md](REFERENCE.md)
```

#### 2. ドメイン別組織

```
cloud-deploy/
├── SKILL.md (ワークフロー + 選択)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

#### 3. 条件付き詳細

```markdown
## Creating documents
Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents
For simple edits, modify XML directly.
**For tracked changes**: See [REDLINING.md](REDLINING.md)
```

### 制約

- **参照は常にSKILL.mdから1レベルの深さに保つ**（ネスト禁止）
- 100行超の参照ファイルには目次を含める
- スクリプトは読み込みなしで実行可能

---

## ワークフロー設計

### チェックリストパターン

複雑な操作は明確な順次ステップに分解し、チェックリストを提供:

```markdown
Task Progress:
- [ ] Step 1: Analyze input
- [ ] Step 2: Create mapping
- [ ] Step 3: Validate
- [ ] Step 4: Execute
- [ ] Step 5: Verify output
```

### フィードバックループ

**バリデータを実行 → エラーを修正 → 繰り返し**

### 計画-検証-実行パターン

バッチ操作や破壊的変更に有効:
1. 中間ファイル（changes.json等）を生成
2. スクリプトで検証
3. 検証通過後に実行

---

## 執筆パターン

### テンプレートパターン

- 厳格な要件: `ALWAYS use this exact template`
- 柔軟な要件: `Here is a sensible default, adjust as needed`

### 例パターン

入力/出力ペアで望ましいスタイルを示す:

```markdown
**Example 1:**
Input: Added user authentication
Output: feat(auth): implement JWT-based authentication
```

### コンテンツガイドライン

- 時間依存情報を避ける（日付ベースの条件分岐禁止）
- 一貫した用語を使用
- 自明な説明を省く（Claudeが既知の情報は不要）
- デフォルトを1つ提供し、エスケープハッチを添える

---

## アンチパターン

| アンチパターン | 問題 | 解決策 |
|---------------|------|--------|
| 深い参照階層 | L3+で読み込み失敗 | 1レベルに平坦化 |
| 曖昧な指示 | 一貫しない動作 | 具体的なMUST/NEVER |
| 過剰な選択肢 | 迷いによる品質低下 | デフォルト1つ+例外 |
| 評価なし開発 | 品質保証なし | 評価駆動開発 |
| ALWAYS/NEVER多用 | WHYが伝わらない | 理由を説明 |

---

## セキュリティ

- 自分で作成 or Anthropicから入手したスキルのみ使用
- 全ファイルを監査（異常なネットワーク呼び出し、ファイルアクセスに注意）
- 外部URLからデータ取得するスキルは特にリスクが高い

---

## Two-Instance開発パターン

```
Claude A（スキル作成）→ Claude B（スキルテスト）→ 観察に基づく改善
```

1. Claude Aとタスク完了 → 再利用パターン特定
2. Claude Aにスキル作成依頼 → 簡潔さレビュー
3. Claude Bでテスト → ギャップ特定
4. 観察に基づき改善

---

## モデル選択

| フェーズ | 推奨 | 理由 |
|----------|------|------|
| スキル設計 | Sonnet/Opus | 構造理解が必要 |
| テスト | Haiku | 高速・低コスト（堅牢性確認） |
| 複雑なテスト | Sonnet | 実際の使用に近い |
| 最終検証 | Opus | 厳格な評価 |

**Tip**: Haikuで機能するスキルは、より大きなモデルでも確実に機能する。

---

**参照元**: [SKILL.md](SKILL.md)
