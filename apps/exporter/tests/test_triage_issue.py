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


# ── Task triage ───────────────────────────────────────────────────────────────

class TestTaskRequiredFields:

    def test_complete_task_routes_to_kanban(self):
        data = base_normalized("task", {"Objective": "Do X", "Requirements": "Req A"})
        result = triage(data)
        assert result["triage_decision"] == "kanban"
        assert result["ready_for_kanban"] is True

    def test_missing_objective_routes_to_needs_info(self):
        data = base_normalized("task", {"Requirements": "Req A"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert result["ready_for_kanban"] is False

    def test_missing_requirements_routes_to_needs_info(self):
        data = base_normalized("task", {"Objective": "Do X"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"

    def test_missing_both_fields_lists_both_in_reason(self):
        data = base_normalized("task", {})
        result = triage(data)
        assert "Objective" in result["triage_reason"]
        assert "Requirements" in result["triage_reason"]

    def test_empty_string_objective_treated_as_missing(self):
        data = base_normalized("task", {"Objective": "  ", "Requirements": "Req A"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"

    def test_triage_reason_set_on_needs_info(self):
        data = base_normalized("task", {})
        result = triage(data)
        assert "triage_reason" in result


# ── Meeting triage ────────────────────────────────────────────────────────────

class TestMeetingRequiredFields:

    def test_complete_meeting_routes_to_kanban(self):
        data = base_normalized("meeting", {
            "Date": "2026-04-01", "Attendees": "Alice, Bob", "Summary": "We met"
        })
        result = triage(data)
        assert result["triage_decision"] == "kanban"

    def test_missing_date_routes_to_needs_info(self):
        data = base_normalized("meeting", {"Attendees": "Alice", "Summary": "S"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert "Date" in result["triage_reason"]

    def test_missing_attendees_routes_to_needs_info(self):
        data = base_normalized("meeting", {"Date": "2026-04-01", "Summary": "S"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert "Attendees" in result["triage_reason"]

    def test_missing_summary_routes_to_needs_info(self):
        data = base_normalized("meeting", {"Date": "2026-04-01", "Attendees": "Alice"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert "Summary" in result["triage_reason"]

    def test_outcomes_not_required(self):
        data = base_normalized("meeting", {
            "Date": "2026-04-01", "Attendees": "Alice", "Summary": "S"
        })
        result = triage(data)
        assert result["triage_decision"] == "kanban"


# ── Decision triage ───────────────────────────────────────────────────────────

class TestDecisionRequiredFields:

    def test_complete_decision_routes_to_kanban(self):
        data = base_normalized("decision", {"Context": "We needed X", "Decision": "Use Y"})
        result = triage(data)
        assert result["triage_decision"] == "kanban"

    def test_missing_context_routes_to_needs_info(self):
        data = base_normalized("decision", {"Decision": "Use Y"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert "Context" in result["triage_reason"]

    def test_missing_decision_routes_to_needs_info(self):
        data = base_normalized("decision", {"Context": "We needed X"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert "Decision" in result["triage_reason"]

    def test_consequences_not_required(self):
        data = base_normalized("decision", {"Context": "C", "Decision": "D"})
        result = triage(data)
        assert result["triage_decision"] == "kanban"


# ── Priority tagging ──────────────────────────────────────────────────────────

class TestTaskPriority:

    def test_explicit_urgent_maps_to_p0(self):
        data = base_normalized("task", {
            "Objective": "Do X", "Requirements": "R", "Priority": "urgent"
        })
        assert triage(data)["priority"] == "p0"

    def test_explicit_high_maps_to_p1(self):
        data = base_normalized("task", {
            "Objective": "Do X", "Requirements": "R", "Priority": "high"
        })
        assert triage(data)["priority"] == "p1"

    def test_explicit_normal_maps_to_p2(self):
        data = base_normalized("task", {
            "Objective": "Do X", "Requirements": "R", "Priority": "normal"
        })
        assert triage(data)["priority"] == "p2"

    def test_explicit_low_maps_to_p3(self):
        data = base_normalized("task", {
            "Objective": "Do X", "Requirements": "R", "Priority": "low"
        })
        assert triage(data)["priority"] == "p3"

    def test_keyword_blocker_infers_p0(self):
        data = base_normalized("task", {
            "Objective": "Fix blocker in auth service", "Requirements": "R"
        })
        assert triage(data)["priority"] == "p0"

    def test_keyword_critical_infers_p0(self):
        data = base_normalized("task", {
            "Objective": "Critical data loss bug", "Requirements": "R"
        })
        assert triage(data)["priority"] == "p0"

    def test_keyword_high_infers_p1(self):
        data = base_normalized("task", {
            "Objective": "High priority refactor", "Requirements": "R"
        })
        assert triage(data)["priority"] == "p1"

    def test_keyword_low_infers_p3(self):
        data = base_normalized("task", {
            "Objective": "Low priority cleanup", "Requirements": "R"
        })
        assert triage(data)["priority"] == "p3"

    def test_no_keyword_defaults_to_p2(self):
        data = base_normalized("task", {
            "Objective": "Refactor the database layer", "Requirements": "R"
        })
        assert triage(data)["priority"] == "p2"

    def test_explicit_priority_overrides_keywords(self):
        data = base_normalized("task", {
            "Objective": "Critical blocker outage", "Requirements": "R",
            "Priority": "low",
        })
        assert triage(data)["priority"] == "p3"

    def test_priority_not_set_for_meeting(self):
        data = base_normalized("meeting", {
            "Date": "2026-04-01", "Attendees": "A", "Summary": "S"
        })
        result = triage(data)
        assert "priority" not in result

    def test_priority_not_set_for_decision(self):
        data = base_normalized("decision", {"Context": "C", "Decision": "D"})
        result = triage(data)
        assert "priority" not in result


# ── Labels output ─────────────────────────────────────────────────────────────

class TestLabels:

    def test_kanban_task_labels(self):
        data = base_normalized("task", {"Objective": "O", "Requirements": "R"})
        result = triage(data)
        assert "intake:task" in result["labels"]
        assert "triage:kanban" in result["labels"]
        assert any(l.startswith("priority:") for l in result["labels"])

    def test_needs_info_task_labels(self):
        data = base_normalized("task", {})
        result = triage(data)
        assert "intake:task" in result["labels"]
        assert "triage:needs-info" in result["labels"]

    def test_kanban_meeting_labels(self):
        data = base_normalized("meeting", {
            "Date": "2026-04-01", "Attendees": "A", "Summary": "S"
        })
        result = triage(data)
        assert "intake:meeting" in result["labels"]
        assert "triage:kanban" in result["labels"]

    def test_kanban_decision_labels(self):
        data = base_normalized("decision", {"Context": "C", "Decision": "D"})
        result = triage(data)
        assert "intake:decision" in result["labels"]
        assert "triage:kanban" in result["labels"]

    def test_p0_task_has_priority_label(self):
        data = base_normalized("task", {
            "Objective": "O", "Requirements": "R", "Priority": "urgent"
        })
        result = triage(data)
        assert "priority:p0" in result["labels"]

    def test_labels_always_present(self):
        for itype, fields in [
            ("task", {}),
            ("meeting", {}),
            ("decision", {}),
        ]:
            data = base_normalized(itype, fields)
            result = triage(data)
            assert "labels" in result
            assert isinstance(result["labels"], list)


# ── Mutation and passthrough ──────────────────────────────────────────────────

class TestTriageMutatesInput:

    def test_returns_same_object(self):
        data = base_normalized("meeting", {
            "Date": "2026-04-01", "Attendees": "A", "Summary": "S"
        })
        assert triage(data) is data

    def test_preserves_existing_fields(self):
        data = base_normalized("task", {"Objective": "O", "Requirements": "R"})
        result = triage(data)
        assert result["source_issue_number"] == 1
        assert result["title"] == "Test issue"
