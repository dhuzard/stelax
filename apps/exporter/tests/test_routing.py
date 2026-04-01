import pytest
from exporter.sync_to_veritas import resolve_channel, DEFAULT_CHANNEL


# Routing rules that match routing.example.json
ROUTING_RULES = [
    {"intake_type": "incident", "priority": ["p0", "p1"], "channel": "incidents"},
    {"intake_type": "incident", "channel": "engineering"},
    {"intake_type": "task", "priority": ["p0"], "channel": "founders"},
    {"intake_type": "task", "channel": "engineering"},
    {"intake_type": "proposal", "channel": "founders"},
    {"intake_type": "decision", "channel": "founders"},
    {"intake_type": "retro", "channel": "operations"},
    {"intake_type": "meeting", "channel": "operations"},
    {"channel": "engineering"},
]


def issue(intake_type, priority=None):
    data = {"intake_type": intake_type}
    if priority is not None:
        data["priority"] = priority
    return data


# ── Incident routing ──────────────────────────────────────────────────────────

class TestIncidentRouting:

    def test_p0_incident_routes_to_incidents_channel(self):
        assert resolve_channel(issue("incident", "p0"), ROUTING_RULES) == "incidents"

    def test_p1_incident_routes_to_incidents_channel(self):
        assert resolve_channel(issue("incident", "p1"), ROUTING_RULES) == "incidents"

    def test_p2_incident_routes_to_engineering(self):
        assert resolve_channel(issue("incident", "p2"), ROUTING_RULES) == "engineering"

    def test_p3_incident_routes_to_engineering(self):
        assert resolve_channel(issue("incident", "p3"), ROUTING_RULES) == "engineering"

    def test_incident_without_priority_routes_to_engineering(self):
        assert resolve_channel(issue("incident"), ROUTING_RULES) == "engineering"


# ── Task routing ──────────────────────────────────────────────────────────────

class TestTaskRouting:

    def test_p0_task_routes_to_founders(self):
        assert resolve_channel(issue("task", "p0"), ROUTING_RULES) == "founders"

    def test_p1_task_routes_to_engineering(self):
        assert resolve_channel(issue("task", "p1"), ROUTING_RULES) == "engineering"

    def test_p2_task_routes_to_engineering(self):
        assert resolve_channel(issue("task", "p2"), ROUTING_RULES) == "engineering"

    def test_p3_task_routes_to_engineering(self):
        assert resolve_channel(issue("task", "p3"), ROUTING_RULES) == "engineering"

    def test_task_without_priority_routes_to_engineering(self):
        assert resolve_channel(issue("task"), ROUTING_RULES) == "engineering"


# ── Proposal / decision routing ───────────────────────────────────────────────

class TestProposalDecisionRouting:

    def test_proposal_routes_to_founders(self):
        assert resolve_channel(issue("proposal", "p1"), ROUTING_RULES) == "founders"

    def test_proposal_without_priority_routes_to_founders(self):
        assert resolve_channel(issue("proposal"), ROUTING_RULES) == "founders"

    def test_decision_routes_to_founders(self):
        assert resolve_channel(issue("decision"), ROUTING_RULES) == "founders"


# ── Operations channel routing ────────────────────────────────────────────────

class TestOperationsRouting:

    def test_retro_routes_to_operations(self):
        assert resolve_channel(issue("retro"), ROUTING_RULES) == "operations"

    def test_meeting_routes_to_operations(self):
        assert resolve_channel(issue("meeting"), ROUTING_RULES) == "operations"


# ── Fallback behaviour ────────────────────────────────────────────────────────

class TestFallback:

    def test_unknown_type_hits_catchall(self):
        assert resolve_channel(issue("unknown_type"), ROUTING_RULES) == "engineering"

    def test_empty_rules_returns_default_channel(self):
        assert resolve_channel(issue("task", "p0"), []) == DEFAULT_CHANNEL

    def test_no_matching_rule_returns_default_channel(self):
        strict_rules = [{"intake_type": "task", "channel": "engineering"}]
        assert resolve_channel(issue("incident", "p0"), strict_rules) == DEFAULT_CHANNEL

    def test_catchall_rule_matches_any_type(self):
        catchall_only = [{"channel": "custom"}]
        for itype in ("task", "meeting", "incident", "retro", "decision", "proposal"):
            assert resolve_channel(issue(itype), catchall_only) == "custom"


# ── Rule evaluation order ─────────────────────────────────────────────────────

class TestRuleOrder:

    def test_first_matching_rule_wins(self):
        rules = [
            {"intake_type": "task", "channel": "first"},
            {"intake_type": "task", "channel": "second"},
        ]
        assert resolve_channel(issue("task"), rules) == "first"

    def test_priority_condition_skips_non_matching_rule(self):
        rules = [
            {"intake_type": "task", "priority": ["p0"], "channel": "high"},
            {"intake_type": "task", "channel": "normal"},
        ]
        assert resolve_channel(issue("task", "p2"), rules) == "normal"
        assert resolve_channel(issue("task", "p0"), rules) == "high"
