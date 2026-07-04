# claude-sessions-sync

Sync Claude Code sessions across all clients (CLI, Cursor, VS Code, Antigravity) so every session appears in every client's session list.

## Problem

Claude Code stores sessions as JSONL files in `~/.claude/projects/`. All clients read these files directly, but they use different strategies:

| Client | Read Strategy | Display Title From |
|--------|--------------|-------------------|
| Cursor / VS Code (older versions) | Full file parse | Any `custom-title` entry in file |
| CLI / Antigravity (newer versions) | First & last 64KB only | `custom-title` in last 64KB, or `firstPrompt` in first 64KB |

Sessions without a `custom-title` entry in the last 64KB may be **invisible** in CLI and Antigravity, especially for large session files where the title data has scrolled out of the tail buffer.

> **Note**: None of these clients use `sessions-index.json` for the session list display.

## Solution

This skill scans all JSONL session files and appends a `{"type":"custom-title","customTitle":"..."}` entry to files that don't have one in the tail. This ensures all clients can find the session title.

Title sources (in priority order):
1. Existing `custom-title` entry found elsewhere in the file (re-appended to tail)
2. First user message (`firstPrompt`) extracted from the file head

## How It Works

```
For each *.jsonl in ~/.claude/projects/<project>/
  ├─ Has custom-title in last 64KB?  → Skip (already OK)
  ├─ Has custom-title elsewhere?     → Re-append to tail
  ├─ Has firstPrompt in first 64KB?  → Append as custom-title
  └─ No user messages at all?        → Skip (empty/ghost session)
```

The script is **idempotent** — running it multiple times is safe. Sessions that already have a `custom-title` in the tail are skipped.

## Usage

### As a Claude Code Skill

```
/claude-sessions-sync
```

### Standalone

```bash
# Preview changes (no modifications)
python3 scripts/sync_sessions.py "/path/to/project" --dry-run

# Sync sessions
python3 scripts/sync_sessions.py "/path/to/project"
```

## Installation

```bash
# Copy to skills directory
cp -r claude-sessions-sync ~/.claude/skills/

# Or create a symlink
ln -s /path/to/claude-sessions-sync ~/.claude/skills/claude-sessions-sync
```

## Requirements

- Python 3.10+
- Claude Code CLI

## File Structure

```
claude-sessions-sync/
├── SKILL.md                    # Skill definition
├── README.md                   # This file
└── scripts/
    └── sync_sessions.py        # Session sync logic
```

## License

Apache 2.0
