# claude-skill-manager

スキルのライフサイクル全体を管理する統合スキル。

## 統合元

| 旧スキル | 役割 | 統合先 |
|---------|------|--------|
| `claude-skill-creation-guide` | 設計原則・パターン | DESIGN-PRINCIPLES.md |
| `agent-skill-manager` | リポジトリ管理・公開 | SKILL.md Phase 5 |
| Anthropic `skill-creator` | 作成・評価・最適化ツール | SKILL.md Phase 1-4 |

## 依存

- Python 3.10+
- PyYAML (`pip install pyyaml`)
- [anthropics/skills](https://github.com/anthropics/skills) リポジトリのローカルクローン

## 構成

```
claude-skill-manager/
├── SKILL.md              # メイン指示（統合ワークフロー）
├── DESIGN-PRINCIPLES.md  # 設計原則詳細リファレンス
└── README.md             # このファイル
```

## Version

- v1.0.0 (2026-03-02): 初版。3スキルを統合
