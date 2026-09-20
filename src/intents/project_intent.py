import re
import time
import os
from src.db import db


class ProjectIntent:

    def __init__(self, brain=None):
        self.brain = brain

    def process(self, user_message, user_id="default_user"):
        message = user_message.strip()
        lower = message.lower()

        # 1. List projects command
        list_patterns = [
            "show my projects", "list my projects", "what are my projects", "my projects",
            "show projects", "list projects", "view projects", "all projects"
        ]
        if any(lower == p or lower.startswith(p) for p in list_patterns):
            projects = db.get_user_projects(user_id)
            if not projects:
                return "You do not have any projects in your Projects Workspace yet. You can create one by saying: *Create project: [Project Name] with description: [Details]*."

            lines = [f"**Your Projects Workspace** ({len(projects)} total)\n"]
            for p in projects:
                name = p.get("name", "Untitled")
                desc = p.get("description") or "No outline added yet."
                lines.append(f"### {name}")
                lines.append(f"{desc}\n")

            return "\n".join(lines).strip()

        # 2. Add / Create project command
        create_match = re.search(
            r'^(?:add|create|start|new)\s+(?:a\s+)?project\s*[:\-]?\s*(.+)$',
            message,
            re.IGNORECASE
        )
        if create_match:
            raw_str = create_match.group(1).strip()

            # Parse name and optional description:
            # "Project Name with description: Outline..." or "Project Name - Outline..." or "Project Name"
            name = raw_str
            desc = ""

            desc_match = re.search(r'\s+(?:with\s+description|details|outline|desc)\s*[:\-]?\s*(.+)$', raw_str, re.IGNORECASE)
            if desc_match:
                desc = desc_match.group(1).strip()
                name = raw_str[:desc_match.start()].strip()
            elif " - " in raw_str:
                parts = raw_str.split(" - ", 1)
                name = parts[0].strip()
                desc = parts[1].strip()

            name = name.strip(' "\'.,')
            if not name:
                return None

            proj_id = "proj_" + str(int(time.time())) + "_" + os.urandom(4).hex()
            db.create_project(proj_id, user_id, name, desc)

            desc_display = desc if desc else "No description specified yet."
            return (
                f"Project created in your Projects Workspace:\n\n"
                f"- **Name**: {name}\n"
                f"- **Outline / Details**: {desc_display}\n\n"
                f"You can view and manage your projects anytime in the **Projects** panel."
            )

        return None
