import re
import time
import os
from src.db import db


class TaskIntent:

    def __init__(self, brain=None):
        self.brain = brain

    def process(self, user_message, user_id="default_user"):
        message = user_message.strip()
        lower = message.lower()

        # 1. Complete / Check off task command
        complete_match = re.search(
            r'^(?:complete|check\s*off|finish|mark|done)\s+(?:task|item)?\s*[:\-]?\s*["\']?([^"\']+)["\']?(?:\s+as\s+(?:done|completed|complete))?$',
            lower
        )
        if complete_match:
            target = complete_match.group(1).strip()
            if target:
                tasks = db.get_user_tasks(user_id)
                for t in tasks:
                    if target == t["id"] or target in t["title"].lower():
                        db.toggle_task(t["id"], user_id, True)
                        return f"Marked task **{t['title']}** as completed in your Checklist."

        # 2. List / Show tasks command
        list_patterns = [
            "show my tasks", "list my tasks", "what are my tasks", "my tasks",
            "show tasks", "list tasks", "my checklist", "view tasks", "pending tasks",
            "what are my pending tasks", "show pending tasks", "list checklist"
        ]
        if any(lower == p or lower.startswith(p) for p in list_patterns):
            tasks = db.get_user_tasks(user_id)
            if not tasks:
                return "You do not have any tasks in your Checklist yet. You can add one by saying: *Add task: [Task Name] under [Category]*."

            total = len(tasks)
            completed_count = sum(1 for t in tasks if t.get("completed"))
            pending_count = total - completed_count
            pct = round((completed_count / total) * 100) if total > 0 else 0

            lines = [
                f"**Your Task Checklist** (Progress: {completed_count}/{total} - {pct}%)\n"
            ]

            pending_tasks = [t for t in tasks if not t.get("completed")]
            completed_tasks = [t for t in tasks if t.get("completed")]

            if pending_tasks:
                lines.append("**Active Tasks:**")
                for t in pending_tasks:
                    tag_str = f" `[{t.get('tag', 'General')}]`" if t.get('tag') else ""
                    lines.append(f"- ○ **{t['title']}**{tag_str}")

            if completed_tasks:
                if pending_tasks:
                    lines.append("")
                lines.append("**Completed Tasks:**")
                for t in completed_tasks:
                    tag_str = f" `[{t.get('tag', 'General')}]`" if t.get('tag') else ""
                    lines.append(f"- ✓ ~~{t['title']}~~{tag_str}")

            return "\n".join(lines)

        # 3. Add / Create task command
        add_match = re.search(
            r'^(?:add|create|new|set)\s+(?:a\s+)?(?:task|todo|checklist\s+item|reminder)\s*[:\-]?\s*(.+)$',
            message,
            re.IGNORECASE
        )
        remind_match = re.search(
            r'^(?:remind\s+me\s+to)\s+(.+)$',
            message,
            re.IGNORECASE
        )

        raw_task_str = None
        if add_match:
            raw_task_str = add_match.group(1).strip()
        elif remind_match:
            raw_task_str = remind_match.group(1).strip()

        if raw_task_str:
            # Check for optional category/tag: "under [tag]", "tag: [tag]", "category: [tag]"
            tag = "General"
            title = raw_task_str

            tag_match = re.search(r'\s+(?:under|tag:|category:)\s+([a-zA-Z0-9_\-\s]+)$', raw_task_str, re.IGNORECASE)
            if tag_match:
                tag_candidate = tag_match.group(1).strip().capitalize()
                title = raw_task_str[:tag_match.start()].strip()
                if tag_candidate:
                    tag = tag_candidate

            # Clean leading/trailing quotes or punctuation
            title = title.strip(' "\'.,')
            if not title:
                return None

            task_id = "task_" + str(int(time.time())) + "_" + os.urandom(4).hex()
            db.create_task(task_id, user_id, title, tag)

            return (
                f"Task added to your Checklist:\n\n"
                f"- **Title**: {title}\n"
                f"- **Category**: {tag}\n"
                f"- **Status**: Pending\n\n"
                f"You can view and check it off anytime in the **Tasks** panel."
            )

        return None
