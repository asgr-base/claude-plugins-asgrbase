---
name: claude-rename-for-cursor
description: Rename the current Claude Code session. Use when user types /claude-rename-for-cursor or wants to rename the current session. Works in Cursor extension where the built-in /rename command is unavailable.
---

# Claude Rename for Cursor

Cursor拡張機能でビルトインの `/rename` コマンドが使えない環境向けのセッションリネームスキル。

## Instructions

1. ユーザーから新しいセッション名を受け取る（`/claude-rename-for-cursor <name>` の引数、または対話で取得）
2. `scripts/rename_session.py` を実行してセッション名を更新する
3. 結果をユーザーに報告する

### 実行手順

```bash
python3 SKILL_DIR/scripts/rename_session.py "<new_name>" "<project_path>"
```

**引数**:
- `<new_name>`: 新しいセッション名（必須）
- `<project_path>`: プロジェクトのルートパス（必須、作業ディレクトリを渡す）

### 引数の取得

**IMPORTANT**: ARGUMENTS で渡された文字列をそのままセッション名として使用すること。独自に解釈・補完・変更してはならない。

- `/claude-rename-for-cursor my-session-name` → `my-session-name` をそのまま使用
- `/claude-rename-for-cursor hook` → `hook` をそのまま使用（勝手に補完しない）
- `/claude-rename-for-cursor` のみ（引数なし）→ AskUserQuestionでセッション名を聞く

### SKILL_DIRの解決

このスキルの `SKILL.md` が存在するディレクトリが `SKILL_DIR`。スクリプトのパスは以下で解決:
```
<SKILL_DIR>/scripts/rename_session.py
```

シンボリックリンク経由でスキルが配置されている場合は、実体パス（`readlink` 等で解決）を使用すること。

### エラーハンドリング

- セッションが見つからない場合: セッションディレクトリまたはJSONLファイルが存在しないケース
- 名前が空の場合: ユーザーに再入力を求める
