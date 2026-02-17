#!/usr/bin/env python3
"""Rename the current Claude Code session in sessions-index.json.

Usage:
    python3 rename_session.py "<new_name>" "<project_path>"

Identifies the current session by finding the most recently modified .jsonl
file in the project's session directory, then updates customTitle in
sessions-index.json.
"""

import json
import os
import sys
from pathlib import Path


def get_session_dir(project_path: str) -> Path:
    """Convert project path to Claude session directory path."""
    # Claude Code encodes project path: / → - , leading /Users → -Users
    encoded = project_path.replace("/", "-")
    if encoded.startswith("-"):
        pass  # already has leading dash
    else:
        encoded = "-" + encoded
    return Path.home() / ".claude" / "projects" / encoded


def find_current_session(session_dir: Path) -> str | None:
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

    # Extract session ID from filename (remove .jsonl extension)
    return jsonl_files[0].stem


def rename_session(session_dir: Path, session_id: str, new_name: str) -> bool:
    """Update customTitle in sessions-index.json."""
    index_path = session_dir / "sessions-index.json"

    if not index_path.exists():
        print(f"Error: sessions-index.json not found at {index_path}", file=sys.stderr)
        return False

    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Find and update the session entry
    found = False
    old_title = ""
    for entry in data.get("entries", []):
        if entry.get("sessionId") == session_id:
            old_title = entry.get("customTitle", "")
            entry["customTitle"] = new_name
            found = True
            break

    if not found:
        # Session not yet in index (common for Cursor extension sessions)
        # Add a new entry with minimal required fields
        jsonl_path = session_dir / f"{session_id}.jsonl"
        stat = jsonl_path.stat() if jsonl_path.exists() else None
        from datetime import datetime, timezone
        new_entry = {
            "sessionId": session_id,
            "fullPath": str(jsonl_path),
            "fileMtime": int(stat.st_mtime * 1000) if stat else 0,
            "firstPrompt": "",
            "customTitle": new_name,
            "summary": "",
            "messageCount": 0,
            "created": datetime.now(timezone.utc).isoformat(),
            "modified": datetime.now(timezone.utc).isoformat(),
            "gitBranch": "",
            "projectPath": "",
            "isSidechain": False,
        }
        data.setdefault("entries", []).append(new_entry)

    # Write back
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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

    session_id = find_current_session(session_dir)
    if not session_id:
        print("Error: No session files found", file=sys.stderr)
        sys.exit(1)

    if rename_session(session_dir, session_id, new_name):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
