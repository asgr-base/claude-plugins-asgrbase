---
name: claude-rename
description: Rename the current Claude Code session. Use when user types /claude-rename or wants to rename the current session. Works in environments where the built-in /rename command is unavailable.
version: 1.0.0
author: asgr-base
createDate: 2026-02-21
updateDate: 2026-02-21
license: Apache-2.0
disable-model-invocation: true
---

# Claude Rename

ビルトインの `/rename` コマンドが使えない環境向けのセッションリネームスキル。

## Instructions

1. ユーザーから新しいセッション名を受け取る（`/claude-rename <name>` の引数、または対話で取得）
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

- `/claude-rename my-session-name` → `my-session-name` をそのまま使用
- `/claude-rename hook` → `hook` をそのまま使用（勝手に補完しない）
- `/claude-rename` のみ（引数なし）→ AskUserQuestionでセッション名を聞く

### SKILL_DIRの解決

このスキルの `SKILL.md` が存在するディレクトリが `SKILL_DIR`。スクリプトのパスは以下で解決:
```
<SKILL_DIR>/scripts/rename_session.py
```

シンボリックリンク経由でスキルが配置されている場合は、実体パス（`readlink` 等で解決）を使用すること。

### エラーハンドリング

- セッションが見つからない場合: セッションディレクトリまたはJSONLファイルが存在しないケース
- 名前が空の場合: ユーザーに再入力を求める
