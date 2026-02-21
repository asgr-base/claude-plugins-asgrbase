#!/usr/bin/env python3
"""Rename the current Claude Code session by appending a custom-title entry to the JSONL file.

Usage:
    python3 rename_session.py "<new_name>" "<project_path>"

Identifies the current session by finding the most recently modified .jsonl
file in the project's session directory, then appends a custom-title entry.

The Cursor extension reads {"type":"custom-title","customTitle":"..."} from
the JSONL file directly (NOT from sessions-index.json).
"""

import json
import sys
from pathlib import Path
from typing import Optional


def get_session_dir(project_path: str) -> Path:
    """Convert project path to Claude session directory path."""
    # Claude Code encodes project path: / → - , leading /Users → -Users
    encoded = project_path.replace("/", "-")
    if not encoded.startswith("-"):
        encoded = "-" + encoded
    return Path.home() / ".claude" / "projects" / encoded


def find_current_session(session_dir: Path) -> Optional[Path]:
    """Find the most recently modified .jsonl session file."""
    jsonl_files = list(session_dir.glob("*.jsonl"))
    if not jsonl_files:
        return None

    # Filter out agent- prefixed files
    jsonl_files = [f for f in jsonl_files if not f.name.startswith("agent-")]

    if not jsonl_files:
        return None

    # Sort by modification time, most recent first
    jsonl_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return jsonl_files[0]


def get_current_title(jsonl_path: Path) -> str:
    """Read the current custom title from the JSONL file."""
    title = ""
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("type") == "custom-title" and obj.get("customTitle"):
                    title = obj["customTitle"]
            except (json.JSONDecodeError, KeyError):
                continue
    return title


def rename_session(jsonl_path: Path, new_name: str) -> bool:
    """Append a custom-title entry to the JSONL session file."""
    old_title = get_current_title(jsonl_path)

    entry = {"type": "custom-title", "customTitle": new_name}
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    session_id = jsonl_path.stem
    if old_title:
        print(f'Renamed: "{old_title}" → "{new_name}"')
    else:
        print(f'Named: "{new_name}"')
    print(f"Session ID: {session_id}")
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: rename_session.py <new_name> <project_path>", file=sys.stderr)
        sys.exit(1)

    new_name = sys.argv[1].strip()
    project_path = sys.argv[2].strip()

    if not new_name:
        print("Error: Session name cannot be empty", file=sys.stderr)
        sys.exit(1)

    session_dir = get_session_dir(project_path)

    if not session_dir.exists():
        print(f"Error: Session directory not found: {session_dir}", file=sys.stderr)
        sys.exit(1)

    jsonl_path = find_current_session(session_dir)
    if not jsonl_path:
        print("Error: No session files found", file=sys.stderr)
        sys.exit(1)

    if rename_session(jsonl_path, new_name):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
