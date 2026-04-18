# learn

セッション振り返りと設定改善提案スキル。会話履歴を分析し、CLAUDE.md・.claude/rules/・.claude/references/・スキル・hooks への具体的な改善提案を生成します。

## インストール

```bash
claude plugin install learn@asgr-base
```

## スキル

### learn

セッション中の発見・問題・訂正を分析し、プロジェクト設定への改善提案を生成します。「また同じ説明をする」「同じ失敗を繰り返す」を防ぐことが目的。

**使用タイミング**:

- `/learn` を実行
- ユーザーが「セッションの振り返り」「学んだことを整理して」「CLAUDE.mdを改善して」「このセッションから何を学ぶ？」「ルールに追加すべきことは？」と言ったとき

**クイックリファレンス**:

| モード | 用途 |
|--------|------|
| `/learn` | フル分析 → 提案 → 承認 → 適用 |
| `/learn quick` | 3行サマリーのみ（ファイル変更なし） |
| `/learn apply` | 提案後、確認なしで即適用 |

## 機能

1. **Phase 1: セッション分析** - 会話履歴から発見・問題・パターンを抽出
2. **Phase 2: 改善対象の探索** - CLAUDE.md・.claude/・スキルの最適な配置先を検討
3. **Phase 3: 改善提案の生成** - 具体的で根拠のある提案を作成
4. **Phase 4: 承認・適用** - ユーザーの確認を取って改善を適用

## 詳細

詳細は [SKILL.md](skills/learn/SKILL.md) を参照。改善対象別の書き込みガイドラインは [references/targets-guide.md](references/targets-guide.md) を参照。

## ライセンス

Apache License 2.0
