# claude-rename

Rename the current Claude Code session in environments where the built-in `/rename` command is unavailable.

## Problem

Claude Code CLI provides a `/rename` command to give sessions human-readable names. However, when using Claude Code through the Cursor (VS Code) extension, built-in slash commands like `/rename` are not supported.

## Solution

This skill registers as `/claude-rename` in Claude Code's skill system, providing session renaming functionality through the Skill tool interface.

## How It Works

1. Locates the session directory at `~/.claude/projects/<encoded-project-path>/`
2. Identifies the current session by finding the most recently modified `.jsonl` file
3. Appends a `{"type":"custom-title","customTitle":"..."}` entry to the JSONL session file

The Cursor extension reads `custom-title` entries directly from JSONL files (not from `sessions-index.json`). No session restart is required — the new name appears when the session panel is refreshed.

## Usage

```
/claude-rename my-session-name
```

If no name is provided, the skill will prompt you interactively.

## Installation

```bash
cp -r claude-rename ~/.claude/skills/
```

Or create a symlink:

```bash
ln -s /path/to/claude-rename ~/.claude/skills/claude-rename
```

## Requirements

- Python 3.10+
- Claude Code CLI

## File Structure

```
claude-rename/
├── SKILL.md                    # Skill definition
├── README.md                   # This file
└── scripts/
    └── rename_session.py       # Session rename logic
```

## Client Behavior: Session Name Resolution

Each Claude Code client reads session names differently. Understanding these differences is critical for reliable renaming.

### How Clients Resolve Session Names

| Client | Name Source | Read Strategy |
|--------|-----------|---------------|
| Claude Code CLI | `sessions-index.json` `customTitle` field | Full JSON parse |
| Cursor Extension | JSONL `custom-title` entry | Head/tail partial read (see below) |
| Antigravity Extension | JSONL `custom-title` entry | Head/tail partial read (see below) |

### Cursor / Antigravity Extension: 64KB Tail Window

The VS Code extensions (Cursor, Antigravity) do **not** read the entire JSONL file when building the session list. For performance, they read only:

- **Head**: First 64KB (65,536 bytes)
- **Tail**: Last 64KB (65,536 bytes)

Session name resolution follows this priority:

```
displayName = searchTail("customTitle") || searchTail("summary") || firstUserMessage(head)
```

The `customTitle` field is searched **only in the tail** (last 64KB). It is NOT searched in the head.

### Known Issue: Title Drift

When a session is renamed, a `custom-title` entry is appended to the end of the JSONL file. As conversation continues, new entries (user messages, assistant responses, system context) accumulate after it, pushing the `custom-title` entry beyond the 64KB tail window.

**Impact**: After 2-3 conversation exchanges (each exchange can add 20-50KB due to system reminders, hook outputs, and tool results), the custom title becomes invisible to the extension. The session list falls back to displaying the first user message instead.

**Why some sessions retain their names**: Sessions that are renamed near the end of their lifecycle (e.g., renamed as the final action) keep the `custom-title` within the tail window. Sessions with repeated rename calls throughout their lifetime also maintain visibility, as the most recent `custom-title` entry stays close to the end.

### Mitigation Strategies

1. **Stop hook** (recommended): Re-append the `custom-title` entry at the end of each assistant turn, keeping it always within the tail window
2. **Periodic compaction**: Use `compact_session.py` to reduce file size, which keeps the title within the readable range
3. **Rename at session end**: Call `/claude-rename` as one of the last actions in a session

### Claude Code CLI Behavior

The CLI reads `sessions-index.json` directly and performs a full JSON parse, so the 64KB limitation does not apply. The `update_sessions_index()` function in `rename_session.py` ensures CLI compatibility.

### Extension Internal Details

The extension code path (observed in Cursor extension v2.1.x):

```javascript
// Session list: reads head + tail buffers
const BUFFER_SIZE = 65536; // 64KB
const head = readBytes(file, 0, BUFFER_SIZE);
const tail = readBytes(file, fileSize - BUFFER_SIZE, BUFFER_SIZE);

// Name resolution: tail-only for customTitle
displayName = extractField(tail, "customTitle")
           || extractField(tail, "summary")
           || extractFirstUserMessage(head);

// Full session load (when opening a session): reads entire file
// custom-title is always found in this path
```

Note: Variable names are illustrative. The actual extension uses minified identifiers.

## License

Apache 2.0
