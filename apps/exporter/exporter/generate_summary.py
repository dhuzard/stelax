import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def get_args():
    parser = argparse.ArgumentParser(
        description="Generate a summary of recently exported memory artifacts."
    )
    parser.add_argument(
        "--memory-dir", required=True, help="Path to local memory repository"
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Number of past days to include (default: 7)"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory to write summary into (default: <memory-dir>/summaries/YYYY/)"
    )
    return parser.parse_args()


def collect_artifacts(memory_dir, since):
    """Walk memory_dir for JSON artifact sidecars exported on or after `since`.

    Returns a list of artifact dicts sorted by export_timestamp ascending.
    Files that are missing required fields or have unparseable timestamps are skipped.
    """
    artifacts = []
    for json_path in Path(memory_dir).rglob("*.json"):
        try:
            with open(json_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        required = ("artifact_id", "type", "export_timestamp",
                    "source_issue_number", "source_issue_url")
        if not all(k in data for k in required):
            continue

        try:
            ts = datetime.fromisoformat(
                data["export_timestamp"].replace("Z", "+00:00")
            )
        except (ValueError, KeyError):
            continue

        if ts >= since:
            artifacts.append(data)

    return sorted(artifacts, key=lambda a: a["export_timestamp"])


def group_by_type(artifacts):
    """Return a dict of {type: [artifact, ...]} preserving insertion order."""
    groups = {}
    for artifact in artifacts:
        t = artifact["type"]
        groups.setdefault(t, []).append(artifact)
    return groups


def render_summary(groups, period_label, generated_at, template_dir):
    """Render the weekly_summary.j2 template with the given data."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        keep_trailing_newline=True,
    )
    template = env.get_template("weekly_summary.j2")
    return template.render(
        period_label=period_label,
        groups=groups,
        total=sum(len(v) for v in groups.values()),
        generated_at=generated_at,
    )


def generate_summary(memory_dir, days=7, output_dir=None):
    """Generate a markdown summary of artifacts exported in the last `days` days.

    Writes the file to output_dir (or <memory_dir>/summaries/YYYY/ by default)
    and returns the path of the written file.
    """
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    period_label = f"{since.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}"

    artifacts = collect_artifacts(memory_dir, since)
    groups = group_by_type(artifacts)

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    content = render_summary(groups, period_label, now.isoformat(), template_dir)

    if output_dir is None:
        output_dir = os.path.join(memory_dir, "summaries", now.strftime("%Y"))
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{now.strftime('%Y-W%V')}-summary.md"
    output_path = os.path.join(output_dir, filename)
    with open(output_path, "w") as f:
        f.write(content)

    print(
        f"Summary written to {output_path} "
        f"({len(artifacts)} artifact(s) across {len(groups)} type(s))"
    )
    return output_path


if __name__ == "__main__":
    args = get_args()
    generate_summary(args.memory_dir, args.days, args.output_dir)
    sys.exit(0)
