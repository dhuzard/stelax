import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from exporter.audit_trail import load_artifacts, build_trail, generate_trails


def make_artifact(tmp_dir, artifact_id, type_="task", issue_number=1, metadata=None, subdir="tasks/2026"):
    path = Path(tmp_dir) / subdir
    path.mkdir(parents=True, exist_ok=True)
    data = {
        "artifact_id": artifact_id,
        "source_issue_number": issue_number,
        "source_issue_url": f"https://github.com/org/repo/issues/{issue_number}",
        "type": type_,
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "content": f"# {artifact_id}",
        "metadata": metadata or {},
    }
    (path / f"{artifact_id}.json").write_text(json.dumps(data))
    return data


# ── load_artifacts ────────────────────────────────────────────────────────────

class TestLoadArtifacts:

    def test_loads_valid_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "a1")
            make_artifact(tmp, "a2", subdir="decisions/2026")
            results = load_artifacts(tmp)
            assert len(results) == 2

    def test_skips_incomplete_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps({"type": "task"}))
            assert load_artifacts(tmp) == []

    def test_skips_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{{not valid}}")
            assert load_artifacts(tmp) == []

    def test_skips_search_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "a1")
            idx = Path(tmp) / "search-index.json"
            idx.write_text(json.dumps({"entries": [], "total": 0, "generated_at": "x"}))
            results = load_artifacts(tmp)
            assert len(results) == 1

    def test_empty_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            assert load_artifacts(tmp) == []


# ── build_trail ───────────────────────────────────────────────────────────────

class TestBuildTrail:

    def _artifact(self, metadata=None):
        return {
            "artifact_id": "test-id",
            "type": "task",
            "source_issue_number": 42,
            "source_issue_url": "https://github.com/org/repo/issues/42",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "content": "",
            "metadata": metadata or {},
        }

    def test_trail_always_starts_with_intake(self):
        events = build_trail(self._artifact())
        assert events[0]["stage"] == "intake"

    def test_trail_always_ends_with_exported(self):
        events = build_trail(self._artifact())
        assert events[-1]["stage"] == "exported"

    def test_exported_event_has_timestamp(self):
        artifact = self._artifact()
        events = build_trail(artifact)
        assert events[-1]["timestamp"] == artifact["export_timestamp"]

    def test_kanban_trail_includes_execution_stage(self):
        artifact = self._artifact(metadata={"triage_decision": "kanban"})
        stages = [e["stage"] for e in build_trail(artifact)]
        assert "execution" in stages

    def test_needs_info_trail_excludes_execution_stage(self):
        artifact = self._artifact(metadata={"triage_decision": "needs-info"})
        stages = [e["stage"] for e in build_trail(artifact)]
        assert "execution" not in stages

    def test_channel_appears_in_execution_label(self):
        artifact = self._artifact(metadata={"triage_decision": "kanban", "channel": "incidents"})
        events = build_trail(artifact)
        exec_event = next(e for e in events if e["stage"] == "execution")
        assert "incidents" in exec_event["label"]

    def test_triage_reason_appears_in_triage_event(self):
        artifact = self._artifact(metadata={
            "triage_decision": "needs-info",
            "triage_reason": "Missing Objective",
        })
        events = build_trail(artifact)
        triage_event = next(e for e in events if e["stage"] == "triage")
        assert "Missing Objective" in triage_event["detail"]

    def test_minimum_trail_length(self):
        # intake + triage + exported = at least 3 events
        assert len(build_trail(self._artifact())) >= 3


# ── generate_trails ───────────────────────────────────────────────────────────

class TestGenerateTrails:

    def test_writes_one_file_per_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "a1")
            make_artifact(tmp, "a2", subdir="decisions/2026")
            paths = generate_trails(tmp)
            assert len(paths) == 2

    def test_output_files_are_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "my-artifact")
            paths = generate_trails(tmp)
            assert all(p.endswith(".md") for p in paths)

    def test_filename_contains_artifact_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "unique-id-42")
            paths = generate_trails(tmp)
            assert any("unique-id-42" in p for p in paths)

    def test_trail_content_contains_issue_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "a1", issue_number=99)
            paths = generate_trails(tmp)
            content = Path(paths[0]).read_text()
            assert "99" in content

    def test_trail_content_contains_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "a1", type_="incident")
            paths = generate_trails(tmp)
            content = Path(paths[0]).read_text()
            assert "Incident" in content

    def test_custom_output_dir_respected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with tempfile.TemporaryDirectory() as out:
                make_artifact(tmp, "a1")
                paths = generate_trails(tmp, output_dir=out)
                assert all(p.startswith(out) for p in paths)

    def test_idempotent_reruns(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "a1")
            paths1 = generate_trails(tmp)
            paths2 = generate_trails(tmp)
            assert paths1 == paths2

    def test_empty_memory_dir_produces_no_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = generate_trails(tmp)
            assert paths == []
