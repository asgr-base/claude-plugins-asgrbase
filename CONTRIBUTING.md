# 貢献ガイドライン

ASGR Agent Skillsへの貢献を歓迎します！

## スキルの追加方法

1. このリポジトリをFork
2. 新しいブランチを作成: `git checkout -b feature/new-skill`
3. `plugins/` ディレクトリに新しいスキルフォルダを作成
4. 必要なファイルを追加:
   - `SKILL.md` (必須): スキル定義とYAMLフロントマター
   - `README.md` (推奨): 詳細なドキュメント
   - その他の補助ファイル (オプション)
5. Pull Requestを作成

## SKILL.md の必須フォーマット

```yaml
---
name: skill-name
description: スキルの説明（50文字程度）
version: 1.0.0
author: your-name
license: Apache-2.0
---

# スキル名

## 使用方法

[Claudeが従う指示をここに記述]
```

## コーディング規約

- スキル名は小文字とハイフンのみ使用 (例: `jp-law-verification`)
- descriptionは簡潔に（50文字以内推奨）
- 日本語と英語の両方でドキュメントを提供することを推奨
- 依存関係がある場合は明記

## テスト

Pull Requestを作成する前に、スキルが正しく動作することを確認してください。

## ライセンス

貢献されたコードはApache License 2.0の下でライセンスされます。
