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


# ── Incident triage ───────────────────────────────────────────────────────────

class TestIncidentRequiredFields:

    def test_complete_incident_routes_to_kanban(self):
        data = base_normalized("incident", {"Severity": "sev1", "Impact": "DB down"})
        result = triage(data)
        assert result["triage_decision"] == "kanban"
        assert result["ready_for_kanban"] is True

    def test_missing_severity_routes_to_needs_info(self):
        data = base_normalized("incident", {"Impact": "DB down"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert "Severity" in result["triage_reason"]

    def test_missing_impact_routes_to_needs_info(self):
        data = base_normalized("incident", {"Severity": "sev0"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert "Impact" in result["triage_reason"]

    def test_resolution_not_required(self):
        data = base_normalized("incident", {"Severity": "sev2", "Impact": "Slow queries"})
        result = triage(data)
        assert result["triage_decision"] == "kanban"

    def test_timeline_not_required(self):
        data = base_normalized("incident", {"Severity": "sev3", "Impact": "Minor lag"})
        result = triage(data)
        assert result["triage_decision"] == "kanban"


class TestIncidentPriority:

    def test_sev0_maps_to_p0(self):
        data = base_normalized("incident", {"Severity": "sev0", "Impact": "I"})
        assert triage(data)["priority"] == "p0"

    def test_sev1_maps_to_p0(self):
        data = base_normalized("incident", {"Severity": "sev1", "Impact": "I"})
        assert triage(data)["priority"] == "p0"

    def test_sev2_maps_to_p1(self):
        data = base_normalized("incident", {"Severity": "sev2", "Impact": "I"})
        assert triage(data)["priority"] == "p1"

    def test_sev3_maps_to_p2(self):
        data = base_normalized("incident", {"Severity": "sev3", "Impact": "I"})
        assert triage(data)["priority"] == "p2"

    def test_severity_with_label_suffix(self):
        # Dropdown value is "sev0 — Complete outage" — first token is used
        data = base_normalized("incident", {
            "Severity": "sev0 — Complete outage", "Impact": "I"
        })
        assert triage(data)["priority"] == "p0"

    def test_incident_priority_label_present(self):
        data = base_normalized("incident", {"Severity": "sev1", "Impact": "I"})
        result = triage(data)
        assert "priority:p0" in result["labels"]


# ── Retro triage ──────────────────────────────────────────────────────────────

class TestRetroRequiredFields:

    def test_complete_retro_routes_to_kanban(self):
        data = base_normalized("retro", {
            "Period": "2026-Q1",
            "What Went Well": "Shipped on time",
            "What Didn't Go Well": "Too many meetings",
        })
        result = triage(data)
        assert result["triage_decision"] == "kanban"
        assert result["ready_for_kanban"] is True

    def test_missing_period_routes_to_needs_info(self):
        data = base_normalized("retro", {
            "What Went Well": "W", "What Didn't Go Well": "D"
        })
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert "Period" in result["triage_reason"]

    def test_missing_went_well_routes_to_needs_info(self):
        data = base_normalized("retro", {
            "Period": "Sprint 1", "What Didn't Go Well": "D"
        })
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert "What Went Well" in result["triage_reason"]

    def test_missing_didnt_go_well_routes_to_needs_info(self):
        data = base_normalized("retro", {
            "Period": "Sprint 1", "What Went Well": "W"
        })
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert "What Didn't Go Well" in result["triage_reason"]

    def test_action_items_not_required(self):
        data = base_normalized("retro", {
            "Period": "Sprint 1",
            "What Went Well": "W",
            "What Didn't Go Well": "D",
        })
        result = triage(data)
        assert result["triage_decision"] == "kanban"

    def test_retro_has_no_priority(self):
        data = base_normalized("retro", {
            "Period": "Sprint 1",
            "What Went Well": "W",
            "What Didn't Go Well": "D",
        })
        result = triage(data)
        assert "priority" not in result


# ── Proposal triage ───────────────────────────────────────────────────────────

class TestProposalRequiredFields:

    def test_complete_proposal_routes_to_kanban(self):
        data = base_normalized("proposal", {
            "Problem": "X is slow", "Proposed Solution": "Use Y"
        })
        result = triage(data)
        assert result["triage_decision"] == "kanban"
        assert result["ready_for_kanban"] is True

    def test_missing_problem_routes_to_needs_info(self):
        data = base_normalized("proposal", {"Proposed Solution": "Use Y"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert "Problem" in result["triage_reason"]

    def test_missing_proposed_solution_routes_to_needs_info(self):
        data = base_normalized("proposal", {"Problem": "X is slow"})
        result = triage(data)
        assert result["triage_decision"] == "needs-info"
        assert "Proposed Solution" in result["triage_reason"]

    def test_alternatives_not_required(self):
        data = base_normalized("proposal", {
            "Problem": "P", "Proposed Solution": "S"
        })
        result = triage(data)
        assert result["triage_decision"] == "kanban"


class TestProposalPriority:

    def test_explicit_urgent_maps_to_p0(self):
        data = base_normalized("proposal", {
            "Problem": "P", "Proposed Solution": "S", "Priority": "urgent"
        })
        assert triage(data)["priority"] == "p0"

    def test_keyword_critical_in_problem_infers_p0(self):
        data = base_normalized("proposal", {
            "Problem": "Critical security gap", "Proposed Solution": "S"
        })
        assert triage(data)["priority"] == "p0"

    def test_keyword_in_proposed_solution_infers_priority(self):
        data = base_normalized("proposal", {
            "Problem": "P", "Proposed Solution": "High priority refactor needed"
        })
        assert triage(data)["priority"] == "p1"

    def test_no_keyword_defaults_to_p2(self):
        data = base_normalized("proposal", {
            "Problem": "Improve deploy pipeline", "Proposed Solution": "Use new tool"
        })
        assert triage(data)["priority"] == "p2"

    def test_proposal_priority_label_present(self):
        data = base_normalized("proposal", {
            "Problem": "P", "Proposed Solution": "S", "Priority": "high"
        })
        result = triage(data)
        assert "priority:p1" in result["labels"]


# ── Labels for new types ──────────────────────────────────────────────────────

class TestNewTypeLabels:

    def test_incident_labels(self):
        data = base_normalized("incident", {"Severity": "sev2", "Impact": "I"})
        result = triage(data)
        assert "intake:incident" in result["labels"]
        assert "triage:kanban" in result["labels"]

    def test_retro_labels(self):
        data = base_normalized("retro", {
            "Period": "Q1", "What Went Well": "W", "What Didn't Go Well": "D"
        })
        result = triage(data)
        assert "intake:retro" in result["labels"]
        assert "triage:kanban" in result["labels"]

    def test_proposal_labels(self):
        data = base_normalized("proposal", {"Problem": "P", "Proposed Solution": "S"})
        result = triage(data)
        assert "intake:proposal" in result["labels"]
        assert "triage:kanban" in result["labels"]
