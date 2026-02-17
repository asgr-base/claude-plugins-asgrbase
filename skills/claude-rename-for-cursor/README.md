# claude-rename-for-cursor

Rename the current Claude Code session from Cursor extension, where the built-in `/rename` command is unavailable.

## Problem

Claude Code CLI provides a `/rename` command to give sessions human-readable names. However, when using Claude Code through the Cursor (VS Code) extension, built-in slash commands like `/rename` are not supported.

## Solution

This skill registers as `/claude-rename-for-cursor` in Claude Code's skill system, providing the same session renaming functionality through the Skill tool interface.

## How It Works

1. Locates the session directory at `~/.claude/projects/<encoded-project-path>/`
2. Identifies the current session by finding the most recently modified `.jsonl` file
3. Appends a `{"type":"custom-title","customTitle":"..."}` entry to the JSONL session file

The Cursor extension reads `custom-title` entries directly from JSONL files (not from `sessions-index.json`). No session restart is required — the new name appears when the session panel is refreshed.

## Usage

```
/claude-rename-for-cursor my-session-name
```

If no name is provided, the skill will prompt you interactively.

## Installation

```bash
cp -r claude-rename-for-cursor ~/.claude/skills/
```

Or create a symlink:

```bash
ln -s /path/to/claude-rename-for-cursor ~/.claude/skills/claude-rename-for-cursor
```

## Requirements

- Python 3.10+
- Claude Code CLI

## File Structure

```
claude-rename-for-cursor/
├── SKILL.md                    # Skill definition
├── README.md                   # This file
└── scripts/
    └── rename_session.py       # Session rename logic
```

## License

Apache 2.0
