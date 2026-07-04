#!/usr/bin/env python3
"""Repair broken parentUuid chains in JSONL session files.

After compaction removes progress entries, some user/assistant messages
have parentUuid pointing to now-missing UUIDs. This script repairs those
links by re-linking to the nearest existing predecessor in file order.

Usage:
    python3 repair_chains.py "<project_path>" [--dry-run]
"""

import json
import os
import sys
from pathlib import Path


def get_session_dir(project_path: str) -> Path:
    """Convert project path to Claude session directory path."""
    encoded = project_path.replace("/", "-")
    if not encoded.startswith("-"):
        encoded = "-" + encoded
    return Path.home() / ".claude" / "projects" / encoded


def repair_file(jsonl_path: Path, dry_run: bool = False) -> dict:
    """Repair broken parentUuid chains in a JSONL file."""
    entries = []
    raw_lines = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            raw_lines.append(line)
            stripped = line.strip()
            if not stripped:
                entries.append(None)
                continue
            try:
                entries.append(json.loads(stripped))
            except (json.JSONDecodeError, ValueError):
                entries.append(None)

    # Build set of all UUIDs present
    all_uuids = set()
    for e in entries:
        if e and e.get("uuid"):
            all_uuids.add(e["uuid"])

    # Find broken links and repair them
    repaired = 0
    last_uuid = None  # Track the last UUID seen in file order (for user/assistant/system)

    new_lines = []
    for i, (entry, raw_line) in enumerate(zip(entries, raw_lines)):
        if entry is None:
            new_lines.append(raw_line)
            continue

        entry_type = entry.get("type", "")
        entry_uuid = entry.get("uuid")
        parent_uuid = entry.get("parentUuid")

        # Check if this entry has a broken parent link
        if parent_uuid and parent_uuid not in all_uuids:
            if entry_type in ("user", "assistant", "system", "attachment"):
                # Re-link to the last known UUID
                entry["parentUuid"] = last_uuid  # May be None for first entry
                new_line = json.dumps(entry, ensure_ascii=False) + "\n"
                new_lines.append(new_line)
                repaired += 1
            else:
                new_lines.append(raw_line)
        else:
            new_lines.append(raw_line)

        # Update last_uuid for entries that have UUIDs and are conversation messages
        if entry_uuid and entry_type in ("user", "assistant", "system", "attachment"):
            last_uuid = entry_uuid

    if not dry_run and repaired > 0:
        with open(jsonl_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    return {
        "file": jsonl_path.name,
        "repaired": repaired,
        "total_uuids": len(all_uuids),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: repair_chains.py <project_path> [--dry-run]", file=sys.stderr)
        sys.exit(1)

    project_path = sys.argv[1].strip()
    dry_run = "--dry-run" in sys.argv

    session_dir = get_session_dir(project_path)
    if not session_dir.exists():
        print(f"Error: Session directory not found: {session_dir}", file=sys.stderr)
        sys.exit(1)

    if dry_run:
        print("=== DRY RUN ===\n")

    jsonl_files = sorted(
        [f for f in session_dir.glob("*.jsonl") if not f.name.startswith("agent-")],
        key=lambda f: f.stat().st_size,
        reverse=True,
    )

    total_repaired = 0
    files_with_issues = 0

    for jsonl_path in jsonl_files:
        stats = repair_file(jsonl_path, dry_run=dry_run)
        if stats["repaired"] > 0:
            files_with_issues += 1
            print(f"{stats['file'][:16]}...  repaired: {stats['repaired']} broken links")
            total_repaired += stats["repaired"]

    if total_repaired == 0:
        print("No broken chains found.")
    else:
        print(f"\nTotal: {total_repaired} links repaired in {files_with_issues} files")


if __name__ == "__main__":
    main()
