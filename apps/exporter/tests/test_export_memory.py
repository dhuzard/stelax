import os
import pytest
import tempfile
from exporter.export_memory import export_artifacts


class TestExportDirectoryStructure:
    """export_artifacts creates the expected year-partitioned directory layout."""

    def test_creates_tasks_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_artifacts(tmpdir)
            assert os.path.isdir(os.path.join(tmpdir, "tasks", "2026"))

    def test_creates_meetings_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_artifacts(tmpdir)
            assert os.path.isdir(os.path.join(tmpdir, "meetings", "2026"))

    def test_creates_decisions_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_artifacts(tmpdir)
            assert os.path.isdir(os.path.join(tmpdir, "decisions", "2026"))

    def test_all_three_top_level_dirs_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_artifacts(tmpdir)
            top_level = os.listdir(tmpdir)
            assert "tasks" in top_level
            assert "meetings" in top_level
            assert "decisions" in top_level

    def test_idempotent_on_repeated_calls(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_artifacts(tmpdir)
            export_artifacts(tmpdir)  # should not raise
            assert os.path.isdir(os.path.join(tmpdir, "tasks", "2026"))

    def test_accepts_nonexistent_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "deep", "memory")
            export_artifacts(nested)
            assert os.path.isdir(os.path.join(nested, "tasks", "2026"))
