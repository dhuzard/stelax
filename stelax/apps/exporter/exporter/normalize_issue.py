import json
import sys
import os

def normalize(parsed_data, source_url, issue_num, intake_type, title):
    """
    Normalizes the parsed issue data into the canonical schema.
    """
    return {
        "source_issue_number": issue_num,
        "source_issue_url": source_url,
        "intake_type": intake_type,
        "title": title,
        "summary": parsed_data.get("Summary", parsed_data.get("Objective", "")),
        "structured_fields": parsed_data,
        "triage_decision": "tbd",
        "ready_for_kanban": False
    }

if __name__ == "__main__":
    # In a real implementation this would read from action inputs/artifacts
    # Provide dummy implementation for the template
    print("Normalizing issue data into canonical format... (Dry Run)")
    sys.exit(0)
