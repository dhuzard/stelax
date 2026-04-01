import json
import sys

# Required fields that must be non-empty for each intake type.
# Missing any of these routes the issue to needs-info.
REQUIRED_FIELDS = {
    "task":     ["Objective", "Requirements"],
    "meeting":  ["Date", "Attendees", "Summary"],
    "decision": ["Context", "Decision"],
    "incident": ["Severity", "Impact"],
    "retro":    ["Period", "What Went Well", "What Didn't Go Well"],
    "proposal": ["Problem", "Proposed Solution"],
}

# Severity level → priority for incidents.
SEVERITY_PRIORITY_MAP = {
    "sev0": "p0",
    "sev1": "p0",
    "sev2": "p1",
    "sev3": "p2",
}

# Intake types that get priority tagging.
PRIORITY_TYPED = {"task", "proposal", "incident"}

# Keyword sets used to infer priority when no explicit Priority field is set.
# Checked in order — first match wins.
PRIORITY_KEYWORDS = {
    "p0": ["critical", "blocker", "outage", "p0", "sev0", "sev1"],
    "p1": ["urgent", "asap", "high priority", "high", "important", "p1"],
    "p3": ["low priority", "low", "minor", "nice to have", "p3"],
}
DEFAULT_PRIORITY = "p2"

# Map from values a submitter might type in the Priority dropdown to canonical levels.
EXPLICIT_PRIORITY_MAP = {
    "urgent": "p0",
    "high":   "p1",
    "normal": "p2",
    "low":    "p3",
    "p0": "p0", "p1": "p1", "p2": "p2", "p3": "p3",
}


def _infer_priority(intake_type, structured_fields):
    """Return a priority level for a prioritisable intake type.

    Incidents derive priority from the Severity field.
    Tasks and proposals use an explicit Priority dropdown with keyword fallback.
    """
    if intake_type == "incident":
        raw = structured_fields.get("Severity", "").strip().lower()
        # Normalise "sev0 — complete outage" → "sev0"
        sev_key = raw.split()[0] if raw else ""
        return SEVERITY_PRIORITY_MAP.get(sev_key, DEFAULT_PRIORITY)

    explicit = structured_fields.get("Priority", "").strip().lower()
    if explicit in EXPLICIT_PRIORITY_MAP:
        return EXPLICIT_PRIORITY_MAP[explicit]

    scan_fields = {
        "task":     ["Objective", "Requirements"],
        "proposal": ["Problem", "Proposed Solution"],
    }
    text = " ".join(
        structured_fields.get(f, "") for f in scan_fields.get(intake_type, [])
    ).lower()

    for level, keywords in PRIORITY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return level

    return DEFAULT_PRIORITY


def _compute_labels(normalized_data, priority=None):
    """Build the list of labels to apply to the GitHub issue."""
    labels = [f"intake:{normalized_data['intake_type']}"]
    decision = normalized_data.get("triage_decision")
    if decision and decision != "tbd":
        labels.append(f"triage:{decision}")
    if priority:
        labels.append(f"priority:{priority}")
    return labels


def triage(normalized_data):
    """Apply deterministic triage rules to a normalized issue.

    Mutates and returns the input dict with triage_decision, ready_for_kanban,
    labels, and (for tasks) priority set.
    """
    intake_type = normalized_data.get("intake_type")
    structured_fields = normalized_data.get("structured_fields", {})

    # Validate required fields for this intake type
    required = REQUIRED_FIELDS.get(intake_type, [])
    missing = [f for f in required if not structured_fields.get(f, "").strip()]

    if missing:
        normalized_data["triage_decision"] = "needs-info"
        normalized_data["triage_reason"] = f"Missing required fields: {', '.join(missing)}"
        normalized_data["ready_for_kanban"] = False
        normalized_data["labels"] = _compute_labels(normalized_data)
        return normalized_data

    # Priority tagging (tasks, proposals, incidents)
    priority = None
    if intake_type in PRIORITY_TYPED:
        priority = _infer_priority(intake_type, structured_fields)
        normalized_data["priority"] = priority

    normalized_data["triage_decision"] = "kanban"
    normalized_data["ready_for_kanban"] = True
    normalized_data["labels"] = _compute_labels(normalized_data, priority)
    return normalized_data


if __name__ == "__main__":
    # In a real implementation this would label the issue via GitHub API
    print("Triaging normalized issue and applying labels... (Dry Run)")
    sys.exit(0)
