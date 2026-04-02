import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def get_args():
    parser = argparse.ArgumentParser(
        description="Generate per-issue audit trail documents from memory artifacts."
    )
    parser.add_argument(
        "--memory-dir", required=True, help="Path to local memory repository"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory to write trails into (default: <memory-dir>/audit/YYYY/)"
    )
    return parser.parse_args()


def load_artifacts(memory_dir):
    """Load all valid artifact JSON sidecars from memory_dir.

    Returns a list of artifact dicts, skipping malformed or incomplete files.
    """
    artifacts = []
    for json_path in sorted(Path(memory_dir).rglob("*.json")):
        if json_path.name in ("search-index.json",):
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

        artifacts.append(data)
    return artifacts


def build_trail(artifact):
    """Construct an ordered list of lifecycle events for a single artifact."""
    events = []

    # Intake event — derive from source issue number and type
    events.append({
        "stage":     "intake",
        "label":     "Issue submitted",
        "detail":    f"#{artifact['source_issue_number']} — {artifact['type']} form",
        "timestamp": None,  # submission timestamp not stored in artifact
    })

    # Triage event
    triage_info = artifact.get("metadata", {}).get("triage_decision", "kanban")
    events.append({
        "stage":     "triage",
        "label":     f"Triaged → {triage_info}",
        "detail":    artifact.get("metadata", {}).get("triage_reason", ""),
        "timestamp": None,
    })

    # Execution / kanban event (only for kanban-routed items)
    if triage_info == "kanban":
        channel = artifact.get("metadata", {}).get("channel", "")
        events.append({
            "stage":     "execution",
            "label":     "Promoted to Veritas" + (f" via {channel}" if channel else ""),
            "detail":    "",
            "timestamp": None,
        })

    # Export event — we have a real timestamp here
    events.append({
        "stage":     "exported",
        "label":     "Exported to memory",
        "detail":    artifact["artifact_id"],
        "timestamp": artifact["export_timestamp"],
    })

    return events


def render_trail(artifact, events, template_dir):
    env = Environment(
        loader=FileSystemLoader(template_dir),
        keep_trailing_newline=True,
    )
    template = env.get_template("audit_trail.j2")
    return template.render(
        artifact=artifact,
        events=events,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def generate_trails(memory_dir, output_dir=None):
    """Generate one audit trail markdown file per artifact in memory_dir.

    Returns the list of output paths written.
    """
    artifacts = load_artifacts(memory_dir)
    template_dir = os.path.join(os.path.dirname(__file__), "templates")

    now = datetime.now(timezone.utc)
    if output_dir is None:
        output_dir = os.path.join(memory_dir, "audit", now.strftime("%Y"))
    os.makedirs(output_dir, exist_ok=True)

    written = []
    for artifact in artifacts:
        events = build_trail(artifact)
        content = render_trail(artifact, events, template_dir)
        filename = f"{artifact['artifact_id']}-trail.md"
        out_path = os.path.join(output_dir, filename)
        with open(out_path, "w") as f:
            f.write(content)
        written.append(out_path)

    print(f"Wrote {len(written)} audit trail(s) to {output_dir}")
    return written


if __name__ == "__main__":
    args = get_args()
    generate_trails(args.memory_dir, args.output_dir)
    sys.exit(0)
