import json
import sys

def triage(normalized_data):
    """
    Applies deterministic triage rules based on the normalized issue data.
    """
    if normalized_data.get("intake_type") == "task":
        if not normalized_data["structured_fields"].get("Objective"):
            normalized_data["triage_decision"] = "needs-info"
            normalized_data["triage_reason"] = "Missing Objective"
            return normalized_data
            
    normalized_data["triage_decision"] = "kanban"
    normalized_data["ready_for_kanban"] = True
    return normalized_data

if __name__ == "__main__":
    # In a real implementation this would label the issue via GitHub API
    print("Triaging normalized issue and applying labels... (Dry Run)")
    sys.exit(0)
