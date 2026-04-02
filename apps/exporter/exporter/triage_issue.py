import json
import sys

# ── Built-in default policy ───────────────────────────────────────────────────
# This is the policy used when no external triage-policy.json is provided.
# Copy configs/triage-policy.example.json to customise without editing code.

DEFAULT_POLICY = {
    "required_fields": {
        "task":     ["Objective", "Requirements"],
        "meeting":  ["Date", "Attendees", "Summary"],
        "decision": ["Context", "Decision"],
        "incident": ["Severity", "Impact"],
        "retro":    ["Period", "What Went Well", "What Didn't Go Well"],
        "proposal": ["Problem", "Proposed Solution"],
    },
    "priority_typed": ["task", "proposal", "incident"],
    "default_priority": "p2",
    "explicit_priority_map": {
        "urgent": "p0",
        "high":   "p1",
        "normal": "p2",
        "low":    "p3",
        "p0": "p0", "p1": "p1", "p2": "p2", "p3": "p3",
    },
    "severity_priority_map": {
        "sev0": "p0",
        "sev1": "p0",
        "sev2": "p1",
        "sev3": "p2",
    },
    "priority_keywords": {
        "p0": ["critical", "blocker", "outage", "p0", "sev0", "sev1"],
        "p1": ["urgent", "asap", "high priority", "high", "important", "p1"],
        "p3": ["low priority", "low", "minor", "nice to have", "p3"],
    },
    "keyword_scan_fields": {
        "task":     ["Objective", "Requirements"],
        "proposal": ["Problem", "Proposed Solution"],
    },
}


def load_policy(path):
    """Load a triage policy from a JSON file, merging over DEFAULT_POLICY.

    Only keys present in the file are overridden — unspecified sections fall
    back to the built-in defaults. Raises ValueError if the file cannot be
    parsed or contains unknown top-level keys.
    """
    with open(path) as f:
        overrides = json.load(f)

    unknown = set(overrides) - set(DEFAULT_POLICY)
    if unknown:
        raise ValueError(f"Unknown policy keys: {', '.join(sorted(unknown))}")

    policy = dict(DEFAULT_POLICY)
    policy.update(overrides)
    return policy


def _infer_priority(intake_type, structured_fields, policy):
    """Return a priority level for a prioritisable intake type."""
    if intake_type == "incident":
        raw = structured_fields.get("Severity", "").strip().lower()
        sev_key = raw.split()[0] if raw else ""
        return policy["severity_priority_map"].get(sev_key, policy["default_priority"])

    explicit = structured_fields.get("Priority", "").strip().lower()
    if explicit in policy["explicit_priority_map"]:
        return policy["explicit_priority_map"][explicit]

    scan_fields = policy["keyword_scan_fields"].get(intake_type, [])
    text = " ".join(structured_fields.get(f, "") for f in scan_fields).lower()

    for level, keywords in policy["priority_keywords"].items():
        if any(kw in text for kw in keywords):
            return level

    return policy["default_priority"]


def _compute_labels(normalized_data, priority=None):
    """Build the list of labels to apply to the GitHub issue."""
    labels = [f"intake:{normalized_data['intake_type']}"]
    decision = normalized_data.get("triage_decision")
    if decision and decision != "tbd":
        labels.append(f"triage:{decision}")
    if priority:
        labels.append(f"priority:{priority}")
    return labels


def triage(normalized_data, policy=None):
    """Apply deterministic triage rules to a normalized issue.

    Accepts an optional policy dict (from load_policy). Defaults to
    DEFAULT_POLICY so all existing behaviour is preserved when no policy
    file is provided.

    Mutates and returns the input dict with triage_decision, ready_for_kanban,
    labels, and (for prioritisable types) priority set.
    """
    if policy is None:
        policy = DEFAULT_POLICY

    intake_type = normalized_data.get("intake_type")
    structured_fields = normalized_data.get("structured_fields", {})

    required = policy["required_fields"].get(intake_type, [])
    missing = [f for f in required if not structured_fields.get(f, "").strip()]

    if missing:
        normalized_data["triage_decision"] = "needs-info"
        normalized_data["triage_reason"] = f"Missing required fields: {', '.join(missing)}"
        normalized_data["ready_for_kanban"] = False
        normalized_data["labels"] = _compute_labels(normalized_data)
        return normalized_data

    priority = None
    if intake_type in policy["priority_typed"]:
        priority = _infer_priority(intake_type, structured_fields, policy)
        normalized_data["priority"] = priority

    normalized_data["triage_decision"] = "kanban"
    normalized_data["ready_for_kanban"] = True
    normalized_data["labels"] = _compute_labels(normalized_data, priority)
    return normalized_data


if __name__ == "__main__":
    print("Triaging normalized issue and applying labels... (Dry Run)")
    sys.exit(0)
