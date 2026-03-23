import os
import requests

class VeritasClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8080"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def create_task(self, title: str, description: str, source_url: str):
        """Creates a task in Veritas"""
        payload = {
            "title": title,
            "description": description,
            "source_url": source_url
        }
        # Dry run for template
        print(f"VeritasClient: Creating task '{title}' from {source_url}")
        return {"id": "dummy-task-id", "status": "created"}
