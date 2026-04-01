import pytest
from exporter.normalize_issue import normalize


SAMPLE_URL = "https://github.com/example-org/example-stelax/issues/42"


class TestNormalizeShape:
    """Output always satisfies the normalized-issue.schema.json required fields."""

    def test_required_keys_present(self):
        result = normalize(
            parsed_data={"Objective": "Build the thing"},
            source_url=SAMPLE_URL,
            issue_num=42,
            intake_type="task",
            title="Build the thing",
        )
        required = {
            "source_issue_number",
            "source_issue_url",
            "intake_type",
            "title",
            "structured_fields",
            "triage_decision",
            "ready_for_kanban",
        }
        assert required.issubset(result.keys())

    def test_initial_triage_decision_is_tbd(self):
        result = normalize({}, SAMPLE_URL, 1, "task", "T")
        assert result["triage_decision"] == "tbd"

    def test_initial_ready_for_kanban_is_false(self):
        result = normalize({}, SAMPLE_URL, 1, "task", "T")
        assert result["ready_for_kanban"] is False

    def test_structured_fields_preserved(self):
        fields = {"Objective": "Do X", "Requirements": "Req A\nReq B"}
        result = normalize(fields, SAMPLE_URL, 5, "task", "Do X")
        assert result["structured_fields"] == fields


class TestNormalizeSummary:
    """Summary field falls back correctly depending on intake type."""

    def test_summary_from_objective_for_task(self):
        result = normalize(
            {"Objective": "Launch rocket"},
            SAMPLE_URL, 1, "task", "Launch rocket",
        )
        assert result["summary"] == "Launch rocket"

    def test_summary_from_summary_field_for_meeting(self):
        result = normalize(
            {"Summary": "Discussed Q2 roadmap"},
            SAMPLE_URL, 2, "meeting", "Q2 Planning",
        )
        assert result["summary"] == "Discussed Q2 roadmap"

    def test_summary_empty_when_no_matching_field(self):
        result = normalize(
            {"Context": "Some context"},
            SAMPLE_URL, 3, "decision", "Adopt Python",
        )
        assert result["summary"] == ""


class TestNormalizePassthrough:
    """Source metadata is passed through unchanged."""

    def test_issue_number_stored(self):
        result = normalize({}, SAMPLE_URL, 99, "meeting", "T")
        assert result["source_issue_number"] == 99

    def test_source_url_stored(self):
        result = normalize({}, SAMPLE_URL, 1, "meeting", "T")
        assert result["source_issue_url"] == SAMPLE_URL

    def test_intake_type_stored(self):
        for itype in ("task", "meeting", "decision"):
            result = normalize({}, SAMPLE_URL, 1, itype, "T")
            assert result["intake_type"] == itype

    def test_title_stored(self):
        result = normalize({}, SAMPLE_URL, 1, "task", "My Title")
        assert result["title"] == "My Title"
