import os
import sys
import argparse

def get_args():
    parser = argparse.ArgumentParser(description="Export finalized STELAX tasks into memory repo format.")
    parser.add_argument("--memory-dir", type=str, required=True, help="Path to local memory repository")
    return parser.parse_args()

def export_artifacts(memory_dir):
    """
    Finds finalized tasks/decisions/meetings and generates sidecar JSON + Markdown artifacts.
    """
    print(f"Exporting finalized artifacts to {memory_dir}...")
    # Generate dummy structure for the template
    os.makedirs(os.path.join(memory_dir, "tasks/2026"), exist_ok=True)
    os.makedirs(os.path.join(memory_dir, "meetings/2026"), exist_ok=True)
    os.makedirs(os.path.join(memory_dir, "decisions/2026"), exist_ok=True)
    
    print("Export completed successfully.")

if __name__ == "__main__":
    args = get_args()
    export_artifacts(args.memory_dir)
    sys.exit(0)
