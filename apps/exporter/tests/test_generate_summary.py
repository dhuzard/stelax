import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from exporter.generate_summary import (
    collect_artifacts,
    group_by_type,
    generate_summary,
)

SAMPLE_URL = "https://github.com/example-org/example-stelax/issues/{n}"


def make_artifact(tmp_dir, artifact_id, type_, export_timestamp, issue_number=1, subdir="tasks/2026"):
    """Write a minimal artifact JSON sidecar into tmp_dir."""
    path = Path(tmp_dir) / subdir
    path.mkdir(parents=True, exist_ok=True)
    data = {
        "artifact_id": artifact_id,
        "source_issue_number": issue_number,
        "source_issue_url": SAMPLE_URL.format(n=issue_number),
        "type": type_,
        "export_timestamp": export_timestamp,
        "content": f"# {artifact_id}",
    }
    out = path / f"{artifact_id}.json"
    out.write_text(json.dumps(data))
    return data


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def days_ago_iso(n):
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


def future_iso(n=1):
    return (datetime.now(timezone.utc) + timedelta(hours=n)).isoformat()


# ── collect_artifacts ─────────────────────────────────────────────────────────

class TestCollectArtifacts:

    def test_returns_artifact_within_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "a1", "task", now_iso())
            since = datetime.now(timezone.utc) - timedelta(days=1)
            results = collect_artifacts(tmp, since)
            assert len(results) == 1
            assert results[0]["artifact_id"] == "a1"

    def test_excludes_artifact_outside_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "old", "task", days_ago_iso(10))
            since = datetime.now(timezone.utc) - timedelta(days=7)
            results = collect_artifacts(tmp, since)
            assert results == []

    def test_includes_artifact_exactly_at_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = datetime.now(timezone.utc) - timedelta(days=7)
            make_artifact(tmp, "boundary", "task", boundary.isoformat())
            results = collect_artifacts(tmp, boundary)
            assert len(results) == 1

    def test_collects_multiple_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "t1", "task", now_iso(), subdir="tasks/2026")
            make_artifact(tmp, "d1", "decision", now_iso(), subdir="decisions/2026")
            make_artifact(tmp, "i1", "incident", now_iso(), subdir="incidents/2026")
            since = datetime.now(timezone.utc) - timedelta(days=1)
            results = collect_artifacts(tmp, since)
            types = {a["type"] for a in results}
            assert types == {"task", "decision", "incident"}

    def test_skips_json_missing_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps({"type": "task"}))  # missing artifact_id etc.
            since = datetime.now(timezone.utc) - timedelta(days=1)
            results = collect_artifacts(tmp, since)
            assert results == []

    def test_skips_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("not json {{{{")
            since = datetime.now(timezone.utc) - timedelta(days=1)
            results = collect_artifacts(tmp, since)
            assert results == []

    def test_skips_artifact_with_invalid_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.json"
            path.write_text(json.dumps({
                "artifact_id": "x", "type": "task",
                "export_timestamp": "not-a-date",
                "source_issue_number": 1,
                "source_issue_url": "https://example.com",
            }))
            since = datetime.now(timezone.utc) - timedelta(days=1)
            assert collect_artifacts(tmp, since) == []

    def test_results_sorted_by_timestamp_ascending(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "newer", "task", now_iso(), subdir="tasks/2026")
            make_artifact(tmp, "older", "task", days_ago_iso(1), subdir="tasks/2026/old")
            since = datetime.now(timezone.utc) - timedelta(days=2)
            results = collect_artifacts(tmp, since)
            assert results[0]["artifact_id"] == "older"
            assert results[1]["artifact_id"] == "newer"

    def test_empty_directory_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            since = datetime.now(timezone.utc) - timedelta(days=7)
            assert collect_artifacts(tmp, since) == []


# ── group_by_type ─────────────────────────────────────────────────────────────

class TestGroupByType:

    def test_groups_single_type(self):
        artifacts = [
            {"type": "task", "artifact_id": "t1"},
            {"type": "task", "artifact_id": "t2"},
        ]
        groups = group_by_type(artifacts)
        assert list(groups.keys()) == ["task"]
        assert len(groups["task"]) == 2

    def test_groups_multiple_types(self):
        artifacts = [
            {"type": "task", "artifact_id": "t1"},
            {"type": "incident", "artifact_id": "i1"},
            {"type": "task", "artifact_id": "t2"},
        ]
        groups = group_by_type(artifacts)
        assert len(groups["task"]) == 2
        assert len(groups["incident"]) == 1

    def test_empty_input_returns_empty_dict(self):
        assert group_by_type([]) == {}

    def test_preserves_insertion_order(self):
        artifacts = [
            {"type": "meeting", "artifact_id": "m1"},
            {"type": "task", "artifact_id": "t1"},
            {"type": "decision", "artifact_id": "d1"},
        ]
        groups = group_by_type(artifacts)
        assert list(groups.keys()) == ["meeting", "task", "decision"]


# ── generate_summary ──────────────────────────────────────────────────────────

class TestGenerateSummary:

    def test_writes_summary_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "t1", "task", now_iso())
            path = generate_summary(tmp, days=7)
            assert os.path.isfile(path)
            assert path.endswith(".md")

    def test_summary_file_in_summaries_subdir(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "t1", "task", now_iso())
            path = generate_summary(tmp, days=7)
            assert "summaries" in path

    def test_summary_contains_artifact_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "my-artifact-id", "task", now_iso())
            path = generate_summary(tmp, days=7)
            content = Path(path).read_text()
            assert "my-artifact-id" in content

    def test_summary_contains_type_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "i1", "incident", now_iso(), subdir="incidents/2026")
            path = generate_summary(tmp, days=7)
            content = Path(path).read_text()
            assert "Incident" in content

    def test_empty_period_renders_no_artifacts_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = generate_summary(tmp, days=7)
            content = Path(path).read_text()
            assert "No artifacts" in content

    def test_respects_custom_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            with tempfile.TemporaryDirectory() as out:
                make_artifact(tmp, "t1", "task", now_iso())
                path = generate_summary(tmp, days=7, output_dir=out)
                assert path.startswith(out)

    def test_excludes_old_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "old", "task", days_ago_iso(30))
            path = generate_summary(tmp, days=7)
            content = Path(path).read_text()
            assert "old" not in content

    def test_idempotent_same_week(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "t1", "task", now_iso())
            path1 = generate_summary(tmp, days=7)
            path2 = generate_summary(tmp, days=7)
            assert path1 == path2  # same filename, overwritten
