import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path


def get_args():
    parser = argparse.ArgumentParser(
        description="Build a search index from exported memory artifacts."
    )
    parser.add_argument(
        "--memory-dir", required=True, help="Path to local memory repository"
    )
    parser.add_argument(
        "--output", default=None,
        help="Output path for search-index.json (default: <memory-dir>/search-index.json)"
    )
    return parser.parse_args()


def _excerpt(text, max_chars=200):
    """Return a plain-text excerpt, truncated at a word boundary."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    return (truncated[:last_space] if last_space > 0 else truncated) + "…"


def index_artifact(data):
    """Convert a memory artifact dict into a search index entry."""
    return {
        "artifact_id":          data["artifact_id"],
        "type":                  data["type"],
        "source_issue_number":   data["source_issue_number"],
        "source_issue_url":      data["source_issue_url"],
        "export_timestamp":      data["export_timestamp"],
        "excerpt":               _excerpt(data.get("content", "")),
        "metadata":              data.get("metadata", {}),
    }


def build_index(memory_dir, output_path=None):
    """Walk memory_dir for artifact JSON sidecars and produce search-index.json.

    Returns the index dict that was written.
    """
    entries = []
    for json_path in sorted(Path(memory_dir).rglob("*.json")):
        # Skip the index file itself on re-runs
        if json_path.name == "search-index.json":
            continue
        try:
            with open(json_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        required = ("artifact_id", "type", "export_timestamp",
                    "source_issue_number", "source_issue_url")
        if not all(k in data for k in required):
            continue

        entries.append(index_artifact(data))

    entries.sort(key=lambda e: e["export_timestamp"], reverse=True)

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total":         len(entries),
        "entries":       entries,
    }

    if output_path is None:
        output_path = os.path.join(memory_dir, "search-index.json")

    with open(output_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"Index written to {output_path} ({len(entries)} entries)")
    return index


if __name__ == "__main__":
    args = get_args()
    build_index(args.memory_dir, args.output)
    sys.exit(0)
