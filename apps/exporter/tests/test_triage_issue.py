import pytest
from exporter.triage_issue import triage


SAMPLE_URL = "https://github.com/example-org/example-stelax/issues/1"


def base_normalized(intake_type, structured_fields=None):
    return {
        "source_issue_number": 1,
        "source_issue_url": SAMPLE_URL,
        "intake_type": intake_type,
        "title": "Test issue",
        "summary": "",
        "structured_fields": structured_fields or {},
        "triage_decision": "tbd",
        "ready_for_kanban": False,
    }


class TestTaskTriage:
    """Tasks are routed based on whether Objective is present."""

    def test_task_with_objective_routes_to_kanban(self):
        data = base_normalized("task", {"Objective": "Build the thing"})
        result = triage(data)
        assert result["triage_decision"] == "kanban"
        assert result["ready_for_kanban"] is True

    def test_task_without_objective_routes_to_needs_info(self):
        data = base_normalized("task", {"Requirements": "Something"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert result["ready_for_kanban"] is False

    def test_task_missing_objective_sets_triage_reason(self):
        data = base_normalized("task", {})
        result = triage(data)
        assert "triage_reason" in result
        assert result["triage_reason"] == "Missing Objective"

    def test_task_with_empty_objective_routes_to_needs_info(self):
        data = base_normalized("task", {"Objective": ""})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"

    def test_task_with_objective_and_extra_fields(self):
        data = base_normalized("task", {
            "Objective": "Do X",
            "Requirements": "Req A",
            "Context": "Some context",
        })
        result = triage(data)
        assert result["triage_decision"] == "kanban"


class TestNonTaskTriage:
    """Meetings and decisions always route to kanban regardless of fields."""

    def test_meeting_routes_to_kanban(self):
        data = base_normalized("meeting", {"Summary": "We discussed things"})
        result = triage(data)
        assert result["triage_decision"] == "kanban"
        assert result["ready_for_kanban"] is True

    def test_decision_routes_to_kanban(self):
        data = base_normalized("decision", {"Decision": "Adopt Python"})
        result = triage(data)
        assert result["triage_decision"] == "kanban"
        assert result["ready_for_kanban"] is True

    def test_meeting_with_no_fields_still_routes_to_kanban(self):
        data = base_normalized("meeting", {})
        result = triage(data)
        assert result["triage_decision"] == "kanban"

    def test_decision_with_no_fields_still_routes_to_kanban(self):
        data = base_normalized("decision", {})
        result = triage(data)
        assert result["triage_decision"] == "kanban"


class TestTriageMutatesInput:
    """Triage updates the dict in place and returns it."""

    def test_returns_same_object(self):
        data = base_normalized("meeting", {"Summary": "S"})
        result = triage(data)
        assert result is data

    def test_preserves_existing_fields(self):
        data = base_normalized("task", {"Objective": "O"})
        result = triage(data)
        assert result["source_issue_number"] == 1
        assert result["title"] == "Test issue"
