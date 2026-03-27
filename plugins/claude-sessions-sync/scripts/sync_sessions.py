#!/usr/bin/env python3
"""Ensure all JSONL session files have a custom-title entry in the tail.

All Claude Code clients (CLI, Cursor, Antigravity) read JSONL files directly.
CLI and Antigravity only read the first/last 64KB of each file. Sessions
without a custom-title entry in the last 64KB may be invisible.

This script scans all JSONL files and appends a custom-title entry to files
that don't have one in the tail, using firstPrompt as the title source.

Usage:
    python3 sync_sessions.py "<project_path>" [--dry-run]
"""

import json
import os
import sys
from pathlib import Path

# CLI/Antigravity read this many bytes from tail
TAIL_BUFFER = 65536


def get_session_dir(project_path: str) -> Path:
    """Convert project path to Claude session directory path."""
    encoded = project_path.replace("/", "-")
    if not encoded.startswith("-"):
        encoded = "-" + encoded
    return Path.home() / ".claude" / "projects" / encoded


def read_tail(path: Path, size: int = TAIL_BUFFER) -> str:
    """Read the last `size` bytes of a file as UTF-8."""
    file_size = path.stat().st_size
    offset = max(0, file_size - size)
    with open(path, "rb") as f:
        f.seek(offset)
        return f.read().decode("utf-8", errors="replace")


def has_custom_title_in_tail(path: Path) -> bool:
    """Check if a custom-title entry exists in the last 64KB."""
    tail = read_tail(path)
    return '"type":"custom-title"' in tail or '"type": "custom-title"' in tail


def extract_first_prompt(path: Path) -> str:
    """Extract the first user message from a JSONL file (head only, fast)."""
    # Read first 64KB for firstPrompt extraction
    with open(path, "rb") as f:
        head = f.read(TAIL_BUFFER).decode("utf-8", errors="replace")

    for line in head.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue

        if obj.get("type") != "user":
            continue

        msg = obj.get("message", {})
        if not isinstance(msg, dict):
            continue

        content = msg.get("content", "")
        if isinstance(content, str) and content.strip():
            return content.strip()[:200]
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text" and c.get("text", "").strip():
                    return c["text"].strip()[:200]

    return ""


def extract_existing_title(path: Path) -> str:
    """Extract custom-title from full file scan (for files that have it somewhere)."""
    title = ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("type") == "custom-title" and obj.get("customTitle"):
                    title = obj["customTitle"]
            except (json.JSONDecodeError, ValueError):
                continue
    return title


def is_sidechain(path: Path) -> bool:
    """Check if the first message is a sidechain session."""
    with open(path, "rb") as f:
        head = f.read(TAIL_BUFFER).decode("utf-8", errors="replace")

    first_line = head.split("\n")[0].strip() if head else ""
    return '"isSidechain":true' in first_line or '"isSidechain": true' in first_line


def sync_sessions(project_path: str, dry_run: bool = False) -> dict:
    """Ensure all sessions have a custom-title entry in the tail.

    Returns a summary dict with counts.
    """
    session_dir = get_session_dir(project_path)

    if not session_dir.exists():
        print(f"Error: Session directory not found: {session_dir}", file=sys.stderr)
        return {"error": True}

    jsonl_files = sorted(
        [f for f in session_dir.glob("*.jsonl") if not f.name.startswith("agent-")],
        key=lambda f: f.stat().st_mtime,
    )

    ok = 0
    added = 0
    skipped = 0
    no_title = 0

    for jsonl_path in jsonl_files:
        # Skip sidechain sessions
        if is_sidechain(jsonl_path):
            skipped += 1
            continue

        # Check if custom-title already in tail
        if has_custom_title_in_tail(jsonl_path):
            ok += 1
            continue

        # Check if there's a custom-title elsewhere in the file (large files)
        existing_title = extract_existing_title(jsonl_path)

        if existing_title:
            # Re-append the existing title to the tail
            title = existing_title
        else:
            # Extract firstPrompt as title
            first_prompt = extract_first_prompt(jsonl_path)
            if not first_prompt:
                no_title += 1
                skipped += 1
                continue

            # Clean up common prefixes from IDE
            title = first_prompt
            for prefix in [
                "<local-command-stdout>",
                "<local-command-caveat>",
                "<session-start-hook>",
                "<ide_opened_file>",
            ]:
                if title.startswith(prefix):
                    # Extract content after tag
                    end_tag = title.find(">", len(prefix) - 1)
                    if end_tag >= 0:
                        remaining = title[end_tag + 1:].strip()
                        if remaining:
                            title = remaining
                    break

            # Truncate for display
            title = title[:100]

        if dry_run:
            size_kb = jsonl_path.stat().st_size / 1024
            label = "[RE-APPEND]" if existing_title else "[ADD]"
            print(f"  {label} {jsonl_path.stem[:8]}... | {size_kb:>8.1f}KB | {title[:60]}")
        else:
            entry = {"type": "custom-title", "customTitle": title}
            with open(jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        added += 1

    return {
        "ok": ok,
        "added": added,
        "skipped": skipped,
        "no_title": no_title,
        "total": len(jsonl_files),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: sync_sessions.py <project_path> [--dry-run]", file=sys.stderr)
        sys.exit(1)

    project_path = sys.argv[1].strip()
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN (no changes will be made) ===\n")

    result = sync_sessions(project_path, dry_run=dry_run)

    if result.get("error"):
        sys.exit(1)

    print(f"\nResults:")
    print(f"  Already OK:  {result['ok']} (custom-title in tail)")
    print(f"  Added:       {result['added']} (custom-title appended)")
    print(f"  Skipped:     {result['skipped']} (sidechain or no extractable title)")
    if result["no_title"] > 0:
        print(f"    (no title: {result['no_title']})")
    print(f"  Total files: {result['total']}")


if __name__ == "__main__":
    main()
