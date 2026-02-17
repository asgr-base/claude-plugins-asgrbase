# claude-rename-for-cursor

Rename the current Claude Code session from Cursor extension, where the built-in `/rename` command is unavailable.

## Problem

Claude Code CLI provides a `/rename` command to give sessions human-readable names. However, when using Claude Code through the Cursor (VS Code) extension, built-in slash commands like `/rename` are not supported.

## Solution

This skill registers as `/rename` in Claude Code's skill system, providing the same session renaming functionality through the Skill tool interface.

## How It Works

1. Locates the session directory at `~/.claude/projects/<encoded-project-path>/`
2. Identifies the current session by finding the most recently modified `.jsonl` file
3. Updates `customTitle` in `sessions-index.json`
4. If the session isn't yet indexed (common for Cursor extension sessions), creates a new entry automatically

## Usage

```
/rename my-session-name
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
