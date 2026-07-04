#!/usr/bin/env python3
"""Compact large JSONL session files by removing non-essential entries.

Usage:
    python3 compact_session.py "<project_path>" [--dry-run] [--min-size-mb N]

Removes entries that are not needed for session resumption:
- progress entries NOT referenced by any parentUuid (safe leaf progress only)
- queue-operation
- system/stop_hook_summary

IMPORTANT: Progress entries that are part of the parentUuid chain
(i.e., referenced by another entry's parentUuid) are PRESERVED to
avoid breaking Cursor extension's transcript building.

Deduplicates:
- custom-title (keeps only the last entry)
- summary (keeps only the last per leafUuid)

Preserves:
- user, assistant messages (conversation content)
- system/compact_boundary (compaction markers)
- file-history-snapshot (file history for undo)
- progress entries in parentUuid chain
- summary (deduplicated)
- custom-title (last only)
"""

import json
import os
import sys
from pathlib import Path

# Entry types safe to remove (not needed for session resume)
REMOVABLE_TYPES = {
    "progress",
    "queue-operation",
}

# System subtypes safe to remove
REMOVABLE_SYSTEM_SUBTYPES = {
    "stop_hook_summary",
}


def get_session_dir(project_path: str) -> Path:
    """Convert project path to Claude session directory path."""
    encoded = project_path.replace("/", "-")
    if not encoded.startswith("-"):
        encoded = "-" + encoded
    return Path.home() / ".claude" / "projects" / encoded


def compact_file(jsonl_path: Path, dry_run: bool = False) -> dict:
    """Compact a single JSONL file. Returns stats dict."""
    original_size = jsonl_path.stat().st_size

    # Phase 1: Read all entries and build parentUuid reference set
    all_entries = []  # (line, parsed_obj_or_None)
    referenced_uuids = set()  # UUIDs referenced by any entry's parentUuid

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
                all_entries.append((line, obj))
                parent = obj.get("parentUuid")
                if parent:
                    referenced_uuids.add(parent)
            except (json.JSONDecodeError, ValueError):
                all_entries.append((line, None))

    # Phase 2: Filter entries, preserving chain-linked progress
    kept_lines = []
    removed_count = 0
    total_count = len(all_entries)
    custom_title_indices = []
    summary_by_leaf = {}

    for line, obj in all_entries:
        if obj is None:
            kept_lines.append(line)
            continue

        entry_type = obj.get("type", "")
        entry_uuid = obj.get("uuid")

        # Remove progress/queue-operation ONLY if not in parentUuid chain
        if entry_type in REMOVABLE_TYPES:
            if entry_uuid and entry_uuid in referenced_uuids:
                # This entry is someone's parent - KEEP it
                kept_lines.append(line)
            else:
                removed_count += 1
            continue

        # Remove specific system subtypes
        if entry_type == "system" and obj.get("subtype") in REMOVABLE_SYSTEM_SUBTYPES:
            removed_count += 1
            continue

        # Track custom-title indices for dedup
        if entry_type == "custom-title":
            custom_title_indices.append(len(kept_lines))

        # Track summary indices for dedup
        if entry_type == "summary":
            leaf_uuid = obj.get("leafUuid", "")
            if leaf_uuid:
                if leaf_uuid in summary_by_leaf:
                    old_idx = summary_by_leaf[leaf_uuid]
                    kept_lines[old_idx] = None
                    removed_count += 1
                summary_by_leaf[leaf_uuid] = len(kept_lines)

        kept_lines.append(line)

    # Deduplicate custom-title: keep only the last one
    if len(custom_title_indices) > 1:
        for idx in custom_title_indices[:-1]:
            if kept_lines[idx] is not None:
                kept_lines[idx] = None
                removed_count += 1

    # Filter out None markers
    kept_lines = [line for line in kept_lines if line is not None]

    new_size = sum(len(line.encode("utf-8")) for line in kept_lines)
    saved = original_size - new_size

    if not dry_run and saved > 0:
        with open(jsonl_path, "w", encoding="utf-8") as f:
            f.writelines(kept_lines)

    return {
        "file": jsonl_path.name,
        "original_size": original_size,
        "new_size": new_size,
        "saved": saved,
        "total_entries": total_count,
        "removed_entries": removed_count,
        "kept_entries": total_count - removed_count,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: compact_session.py <project_path> [--dry-run] [--min-size-mb N]", file=sys.stderr)
        sys.exit(1)

    project_path = sys.argv[1].strip()
    dry_run = "--dry-run" in sys.argv
    min_size_mb = 5  # Default: only compact files > 5MB

    for i, arg in enumerate(sys.argv):
        if arg == "--min-size-mb" and i + 1 < len(sys.argv):
            try:
                min_size_mb = float(sys.argv[i + 1])
            except ValueError:
                pass

    session_dir = get_session_dir(project_path)
    if not session_dir.exists():
        print(f"Error: Session directory not found: {session_dir}", file=sys.stderr)
        sys.exit(1)

    min_size = int(min_size_mb * 1024 * 1024)

    jsonl_files = sorted(
        [f for f in session_dir.glob("*.jsonl")
         if not f.name.startswith("agent-") and f.stat().st_size > min_size],
        key=lambda f: f.stat().st_size,
        reverse=True,
    )

    if not jsonl_files:
        print(f"No JSONL files > {min_size_mb}MB found.")
        sys.exit(0)

    if dry_run:
        print("=== DRY RUN (no changes will be made) ===\n")

    total_saved = 0
    total_removed = 0

    for jsonl_path in jsonl_files:
        stats = compact_file(jsonl_path, dry_run=dry_run)
        saved_mb = stats["saved"] / 1024 / 1024
        orig_mb = stats["original_size"] / 1024 / 1024
        new_mb = stats["new_size"] / 1024 / 1024
        pct = (stats["saved"] / stats["original_size"] * 100) if stats["original_size"] > 0 else 0

        print(f"{stats['file'][:12]}...  {orig_mb:.1f}MB → {new_mb:.1f}MB  "
              f"(-{saved_mb:.1f}MB, -{pct:.0f}%)  "
              f"entries: {stats['total_entries']} → {stats['kept_entries']} "
              f"(-{stats['removed_entries']})")

        total_saved += stats["saved"]
        total_removed += stats["removed_entries"]

    print(f"\nTotal: -{total_saved / 1024 / 1024:.1f}MB saved, {total_removed} entries removed")


if __name__ == "__main__":
    main()
