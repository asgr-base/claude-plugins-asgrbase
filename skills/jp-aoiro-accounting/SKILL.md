---
name: jp-aoiro-accounting
description: 日本の個人事業主向け青色申告帳簿をMarkdown + Pythonで作成。仕訳帳の記帳、帳簿生成（総勘定元帳・残高試算表）、決算書作成（損益計算書・貸借対照表）、減価償却・家事按分計算を支援。青色申告、帳簿、仕訳、記帳、決算書関連の質問時に使用。
version: 1.1.0
author: claude_code
createDate: 2026-02-11
updateDate: 2026-02-11
---

# jp-aoiro-accounting: 青色申告帳簿作成スキル

Markdownテーブルで仕訳帳を管理し、Pythonスクリプトで帳簿・決算書を自動生成する。
e-Taxへの手入力で青色申告（最大65万円控除、令和9年分以降は最大75万円控除）を完了できる。

## クイックリファレンス

| タスク | コマンド |
|--------|---------|
| バリデーション | `python3 scripts/aoiro.py validate <仕訳帳.md>` |
| 帳簿生成 | `python3 scripts/aoiro.py generate <仕訳帳.md> --output-dir <出力先>` |
| 決算書生成 | `python3 scripts/aoiro.py settlement <仕訳帳.md> --output-dir <出力先>` |
| 減価償却計算 | `python3 scripts/aoiro.py depreciation <固定資産台帳.md> --year <年>` |
| 家事按分計算 | `python3 scripts/aoiro.py allocation <仕訳帳.md> --config <家事按分設定.md>` |
| 新年度初期化 | `python3 scripts/aoiro.py init --year <年> --output-dir <出力先>` |

## 日常の記帳ワークフロー

1. **仕訳入力**: 仕訳帳.mdのテーブルに行を追加
2. **バリデーション**: `validate` で貸借一致・科目チェック
3. **帳簿確認**: `generate` で総勘定元帳・残高試算表を生成

## 仕訳入力ルール

仕訳帳はMarkdownテーブル形式。6列固定:

```markdown
| 日付 | 借方科目 | 借方金額 | 貸方科目 | 貸方金額 | 摘要 |
|------|---------|---------|---------|---------|------|
| 2025-09-30 | 売掛金 | 461,175 | 売上高 | 461,175 | A社 9月分報酬 |
```

**ルール**:
- 日付: `YYYY-MM-DD` 形式
- 金額: カンマ区切り可（`461,175` or `461175`）
- 科目: 科目マスタ.mdに定義された科目名を使用
- 各行の借方金額 = 貸方金額（貸借一致）
- 複合仕訳: 同日・同摘要で複数行に分割

## 決算処理フロー（年次）

```
1. 通常仕訳の入力完了を確認
   ↓
2. python3 scripts/aoiro.py validate <仕訳帳.md>
   → エラーがあれば修正
   ↓
3. python3 scripts/aoiro.py depreciation <固定資産台帳.md> --year <年>
   → 出力された決算仕訳を仕訳帳に追記
   ↓
4. python3 scripts/aoiro.py allocation <仕訳帳.md> --config <家事按分設定.md>
   → 出力された決算仕訳を仕訳帳に追記
   ↓
5. python3 scripts/aoiro.py validate <仕訳帳.md>
   → 決算仕訳含めて再検証
   ↓
6. python3 scripts/aoiro.py generate <仕訳帳.md> --output-dir <出力先>
   → 総勘定元帳・残高試算表を生成
   ↓
7. python3 scripts/aoiro.py settlement <仕訳帳.md> --output-dir <出力先>
   → 損益計算書・貸借対照表を生成
   ↓
8. 生成された決算書の数値をe-Taxに手入力
```

## ファイル構成

ユーザーの会計データディレクトリ:

```
accounting/
├── 2025/
│   ├── 仕訳帳.md          ← 日常の記帳
│   ├── 科目マスタ.md       ← 勘定科目定義
│   ├── 固定資産台帳.md     ← 減価償却対象資産
│   ├── 家事按分設定.md     ← 按分率設定
│   └── output/            ← 生成される帳簿
│       ├── 総勘定元帳.md
│       ├── 残高試算表.md
│       ├── 損益計算書.md
│       └── 貸借対照表.md
└── 2026/
    └── ...
```

## セットアップ

1. テンプレートから会計データを初期化:
   ```bash
   python3 scripts/aoiro.py init --year 2025 --output-dir ~/accounting/2025
   ```
2. 科目マスタ.mdを必要に応じてカスタマイズ
3. 仕訳帳.mdの設定セクション（期間）を調整
4. 記帳開始

## 前提条件

- Python 3.8以上（標準ライブラリのみ使用、追加パッケージ不要）
- テキストエディタ（Obsidian、Cursor、VS Code等）

## 参照ドキュメント

| ファイル | 内容 |
|----------|------|
| [REFERENCE.md](REFERENCE.md) | 勘定科目体系・仕訳パターン集・決算書対応表 |
| [README.md](README.md) | セットアップ手順・使い方 |
| [scripts/README.md](scripts/README.md) | スクリプト詳細仕様 |
| [templates/](templates/) | 初期化テンプレート |

## 注意事項

- 本ツールは帳簿作成の補助ツールであり、税務申告の正確性は利用者の責任
- 消費税（インボイス制度）には非対応（免税事業者を想定）。課税事業者の場合は別途消費税処理が必要
- 不明な税務処理は税理士に相談を推奨
- e-Taxへの電子申告は手入力で行う（API連携なし）
- 税制改正により控除額・計算方法が変更される場合がある。確定申告前に最新の法令を確認すること

## 法令準拠

- **帳簿形式**: 正規の簿記（複式簿記）に対応（所得税法 第148条、第149条）
- **減価償却**: 定額法（所得税法施行令 第129条）、非業務用資産転用（同 第135条）に対応
- **青色申告特別控除**: 本ツールで65万円控除の帳簿要件を満たす（租税特別措置法 第25条の2）
- **電子帳簿保存法**: 本ツール自体は電子帳簿保存法の「優良な電子帳簿」要件を直接満たすものではない。75万円控除（令和9年分以降）を受けるには別途対応が必要
- **詳細**: [REFERENCE.md](REFERENCE.md) の「適用法令・税制改正情報」を参照

---

**Version**: 1.1.0
**Last Updated**: 2026-02-11
