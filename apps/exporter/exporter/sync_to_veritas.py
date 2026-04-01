import os
import sys

DEFAULT_CHANNEL = "engineering"


def resolve_channel(normalized_data, routing_rules):
    """Return the NanoClaw channel ID for a triaged issue.

    Rules are evaluated top-to-bottom; the first matching rule wins.
    A rule matches when every condition present in the rule matches the issue:
      - intake_type  (str)  — matches normalized_data["intake_type"]
      - priority     (list) — matches if normalized_data.get("priority") is in the list

    A rule with no conditions (only "channel") acts as a catch-all fallback.
    If no rule matches, DEFAULT_CHANNEL is returned.
    """
    intake_type = normalized_data.get("intake_type", "")
    priority = normalized_data.get("priority")

    for rule in routing_rules:
        if "intake_type" in rule and rule["intake_type"] != intake_type:
            continue
        if "priority" in rule and priority not in rule["priority"]:
            continue
        return rule["channel"]

    return DEFAULT_CHANNEL


def sync_kanban_issues():
    """
    Finds GitHub issues with the 'kanban' label and syncs them to Veritas.
    """
    print("Fetching kanban issues from GitHub...")
    # Fetch from github (dummy)
    issues = [{"title": "Example Task", "url": "https://github.com/org/stelax/issues/1"}]

    print("Syncing to Veritas...")
    # Sync via client (dummy)
    for issue in issues:
        print(f"Synced {issue['title']}")


if __name__ == "__main__":
    sync_kanban_issues()
    sys.exit(0)
