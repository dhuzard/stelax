import json
import os
import tempfile

import pytest
from exporter.triage_issue import triage, load_policy, DEFAULT_POLICY

SAMPLE_URL = "https://github.com/example-org/example-stelax/issues/1"


def base(intake_type, fields=None):
    return {
        "source_issue_number": 1,
        "source_issue_url": SAMPLE_URL,
        "intake_type": intake_type,
        "title": "T",
        "summary": "",
        "structured_fields": fields or {},
        "triage_decision": "tbd",
        "ready_for_kanban": False,
    }


def write_policy(tmp_dir, data):
    path = os.path.join(tmp_dir, "triage-policy.json")
    with open(path, "w") as f:
        json.dump(data, f)
    return path


# ── load_policy ───────────────────────────────────────────────────────────────

class TestLoadPolicy:

    def test_loads_valid_policy_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_policy(tmp, {"default_priority": "p1"})
            policy = load_policy(path)
            assert policy["default_priority"] == "p1"

    def test_unspecified_keys_fall_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_policy(tmp, {"default_priority": "p1"})
            policy = load_policy(path)
            assert policy["required_fields"] == DEFAULT_POLICY["required_fields"]
            assert policy["priority_keywords"] == DEFAULT_POLICY["priority_keywords"]

    def test_raises_on_unknown_top_level_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_policy(tmp, {"unknown_key": "value"})
            with pytest.raises(ValueError, match="Unknown policy keys"):
                load_policy(path)

    def test_raises_on_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.json")
            with open(path, "w") as f:
                f.write("not json {{{")
            with pytest.raises(Exception):
                load_policy(path)

    def test_empty_object_returns_full_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_policy(tmp, {})
            policy = load_policy(path)
            assert policy == DEFAULT_POLICY


# ── Custom required_fields ────────────────────────────────────────────────────

class TestCustomRequiredFields:

    def test_custom_required_field_enforced(self):
        policy = dict(DEFAULT_POLICY)
        policy["required_fields"] = {
            "task": ["Objective", "Requirements", "Owner"],
        }
        data = base("task", {"Objective": "O", "Requirements": "R"})
        result = triage(data, policy=policy)
        assert result["triage_decision"] == "needs-info"
        assert "Owner" in result["triage_reason"]

    def test_removing_required_field_allows_kanban(self):
        policy = dict(DEFAULT_POLICY)
        policy["required_fields"] = {"task": ["Objective"]}
        data = base("task", {"Objective": "O"})
        result = triage(data, policy=policy)
        assert result["triage_decision"] == "kanban"

    def test_unknown_type_with_no_required_fields_routes_to_kanban(self):
        policy = dict(DEFAULT_POLICY)
        policy["required_fields"] = {}
        data = base("task", {})
        result = triage(data, policy=policy)
        assert result["triage_decision"] == "kanban"


# ── Custom priority rules ─────────────────────────────────────────────────────

class TestCustomPriorityKeywords:

    def test_custom_keyword_triggers_correct_level(self):
        policy = dict(DEFAULT_POLICY)
        policy["priority_keywords"] = {"p0": ["fire", "alarm"], "p1": [], "p3": []}
        data = base("task", {"Objective": "fire in production", "Requirements": "R"})
        result = triage(data, policy=policy)
        assert result["priority"] == "p0"

    def test_removed_keyword_no_longer_triggers(self):
        policy = dict(DEFAULT_POLICY)
        policy["priority_keywords"] = {"p0": [], "p1": [], "p3": []}
        data = base("task", {"Objective": "critical blocker outage", "Requirements": "R"})
        result = triage(data, policy=policy)
        assert result["priority"] == policy["default_priority"]

    def test_custom_default_priority_used_as_fallback(self):
        policy = dict(DEFAULT_POLICY)
        policy["default_priority"] = "p1"
        policy["priority_keywords"] = {"p0": [], "p3": []}
        data = base("task", {"Objective": "routine work", "Requirements": "R"})
        result = triage(data, policy=policy)
        assert result["priority"] == "p1"


# ── Custom priority_typed ─────────────────────────────────────────────────────

class TestCustomPriorityTyped:

    def test_adding_meeting_to_priority_typed(self):
        policy = dict(DEFAULT_POLICY)
        policy["priority_typed"] = ["task", "proposal", "incident", "meeting"]
        policy["keyword_scan_fields"] = dict(DEFAULT_POLICY["keyword_scan_fields"])
        policy["keyword_scan_fields"]["meeting"] = ["Summary"]
        data = base("meeting", {
            "Date": "2026-04-01", "Attendees": "A",
            "Summary": "critical architecture review",
        })
        result = triage(data, policy=policy)
        assert "priority" in result

    def test_removing_task_from_priority_typed(self):
        policy = dict(DEFAULT_POLICY)
        policy["priority_typed"] = ["incident"]
        data = base("task", {"Objective": "O", "Requirements": "R"})
        result = triage(data, policy=policy)
        assert "priority" not in result


# ── Custom severity map ───────────────────────────────────────────────────────

class TestCustomSeverityMap:

    def test_custom_severity_priority_mapping(self):
        policy = dict(DEFAULT_POLICY)
        policy["severity_priority_map"] = {
            "sev0": "p0", "sev1": "p1", "sev2": "p2", "sev3": "p3"
        }
        data = base("incident", {"Severity": "sev1", "Impact": "I"})
        result = triage(data, policy=policy)
        assert result["priority"] == "p1"  # default maps sev1→p0, custom maps sev1→p1


# ── Policy loaded from file and passed to triage ─────────────────────────────

class TestEndToEndWithPolicyFile:

    def test_policy_file_overrides_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_policy(tmp, {
                "required_fields": {"task": ["Objective"]}
            })
            policy = load_policy(path)
            # Should pass without Requirements
            data = base("task", {"Objective": "O"})
            result = triage(data, policy=policy)
            assert result["triage_decision"] == "kanban"

    def test_policy_file_custom_keywords(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_policy(tmp, {
                "priority_keywords": {"p0": ["showstopper"], "p1": [], "p3": []}
            })
            policy = load_policy(path)
            data = base("task", {
                "Objective": "showstopper regression", "Requirements": "R"
            })
            result = triage(data, policy=policy)
            assert result["priority"] == "p0"
