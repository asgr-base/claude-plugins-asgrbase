---
name: claude-sessions-sync
description: Sync Claude Code sessions across all clients (CLI, Cursor, Antigravity). Ensures all JSONL session files have a custom-title entry readable by all clients. Use when sessions are missing from resume picker or session list.
---

# Claude Sessions Sync

全クライアント（CLI, Cursor, Antigravity）でセッション一覧を統一する。

## Background

Claude Codeのクライアントはすべて JSONL ファイルを直接読み取るが、読み取り方式が異なる:

| クライアント | 読み取り方式 | 非表示条件 |
|-------------|-------------|-----------|
| Cursor (旧版) | 全ファイルパース | `isSidechain` のみ |
| CLI / Antigravity | 先頭・末尾64KBのみ | タイトル抽出不可で非表示 |

末尾64KBに `custom-title` エントリがないセッションは CLI/Antigravity で非表示になる。
このスキルは全 JSONL ファイルの末尾に `custom-title` エントリを確保する。

## Instructions

### 実行手順

```bash
python3 SKILL_DIR/scripts/sync_sessions.py "<project_path>"
```

**引数**:
- `<project_path>`: プロジェクトのルートパス（必須）

### オプション

| フラグ | 説明 |
|--------|------|
| `--dry-run` | 変更せずに追加対象を表示 |

### 使用例

```bash
# ドライランで確認
python3 SKILL_DIR/scripts/sync_sessions.py "/path/to/project" --dry-run

# 同期実行
python3 SKILL_DIR/scripts/sync_sessions.py "/path/to/project"
```

### SKILL_DIRの解決

シンボリックリンク経由の場合は `readlink` 等で実体パスを解決すること。
