import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from exporter.build_index import build_index, index_artifact, _excerpt


def make_artifact(tmp_dir, artifact_id, type_, issue_number=1, content="Some content", subdir="tasks/2026"):
    path = Path(tmp_dir) / subdir
    path.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    data = {
        "artifact_id": artifact_id,
        "source_issue_number": issue_number,
        "source_issue_url": f"https://github.com/org/repo/issues/{issue_number}",
        "type": type_,
        "export_timestamp": ts,
        "content": content,
    }
    (path / f"{artifact_id}.json").write_text(json.dumps(data))
    return data


# ── _excerpt ──────────────────────────────────────────────────────────────────

class TestExcerpt:

    def test_short_text_returned_unchanged(self):
        assert _excerpt("Hello world") == "Hello world"

    def test_long_text_truncated_at_word_boundary(self):
        text = "word " * 60
        result = _excerpt(text, max_chars=20)
        assert len(result) <= 21  # 20 chars + ellipsis char
        assert result.endswith("…")
        assert not result.endswith(" …")

    def test_empty_string_returns_empty(self):
        assert _excerpt("") == ""

    def test_none_returns_empty(self):
        assert _excerpt(None) == ""

    def test_exact_length_not_truncated(self):
        text = "a" * 200
        assert _excerpt(text, max_chars=200) == text


# ── index_artifact ────────────────────────────────────────────────────────────

class TestIndexArtifact:

    def test_required_keys_present(self):
        data = {
            "artifact_id": "a1",
            "type": "task",
            "source_issue_number": 1,
            "source_issue_url": "https://example.com",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "content": "Some content here",
        }
        entry = index_artifact(data)
        for key in ("artifact_id", "type", "source_issue_number",
                    "source_issue_url", "export_timestamp", "excerpt", "metadata"):
            assert key in entry

    def test_excerpt_populated_from_content(self):
        data = {
            "artifact_id": "a1", "type": "task",
            "source_issue_number": 1,
            "source_issue_url": "https://example.com",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "content": "Detailed description of the task",
        }
        entry = index_artifact(data)
        assert "Detailed description" in entry["excerpt"]

    def test_metadata_defaults_to_empty_dict(self):
        data = {
            "artifact_id": "a1", "type": "task",
            "source_issue_number": 1,
            "source_issue_url": "https://example.com",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "content": "",
        }
        entry = index_artifact(data)
        assert entry["metadata"] == {}


# ── build_index ───────────────────────────────────────────────────────────────

class TestBuildIndex:

    def test_writes_index_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "a1", "task")
            idx = build_index(tmp)
            assert os.path.isfile(os.path.join(tmp, "search-index.json"))

    def test_index_contains_correct_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "a1", "task")
            make_artifact(tmp, "a2", "decision", subdir="decisions/2026")
            idx = build_index(tmp)
            assert idx["total"] == 2

    def test_index_entries_sorted_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            older_ts = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            newer_ts = datetime.now(timezone.utc).isoformat()

            p1 = Path(tmp) / "tasks/2026"
            p1.mkdir(parents=True, exist_ok=True)
            (p1 / "older.json").write_text(json.dumps({
                "artifact_id": "older", "type": "task",
                "source_issue_number": 1,
                "source_issue_url": "https://example.com/1",
                "export_timestamp": older_ts, "content": "",
            }))
            p2 = Path(tmp) / "tasks/2026/new"
            p2.mkdir(parents=True, exist_ok=True)
            (p2 / "newer.json").write_text(json.dumps({
                "artifact_id": "newer", "type": "task",
                "source_issue_number": 2,
                "source_issue_url": "https://example.com/2",
                "export_timestamp": newer_ts, "content": "",
            }))

            idx = build_index(tmp)
            assert idx["entries"][0]["artifact_id"] == "newer"
            assert idx["entries"][1]["artifact_id"] == "older"

    def test_skips_incomplete_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps({"type": "task"}))
            idx = build_index(tmp)
            assert idx["total"] == 0

    def test_skips_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{{not json}}")
            idx = build_index(tmp)
            assert idx["total"] == 0

    def test_does_not_index_itself_on_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "a1", "task")
            build_index(tmp)   # first run writes search-index.json
            idx = build_index(tmp)  # second run must skip it
            assert idx["total"] == 1

    def test_custom_output_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "a1", "task")
            out = os.path.join(tmp, "custom-index.json")
            build_index(tmp, output_path=out)
            assert os.path.isfile(out)

    def test_empty_directory_produces_empty_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx = build_index(tmp)
            assert idx["total"] == 0
            assert idx["entries"] == []

    def test_index_has_generated_at(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx = build_index(tmp)
            assert "generated_at" in idx

    def test_index_file_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_artifact(tmp, "a1", "task")
            build_index(tmp)
            with open(os.path.join(tmp, "search-index.json")) as f:
                parsed = json.load(f)
            assert "entries" in parsed
