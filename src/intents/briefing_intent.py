import datetime
from src.db import db


class BriefingIntent:

    def __init__(self, brain=None):
        self.brain = brain

    def process(self, user_message, user_id="default_user"):
        message = user_message.lower().strip()

        briefing_keywords = [
            "daily briefing", "morning briefing", "daily summary", "daily update",
            "morning update", "today briefing", "what is on my agenda today",
            "what's on my agenda today", "agenda today", "today's agenda",
            "today summary", "briefing today", "give me my briefing", "give me my daily briefing",
            "executive briefing", "my briefing"
        ]

        is_briefing = any(kw in message for kw in briefing_keywords) or (
            ("briefing" in message or "agenda" in message) and any(w in message for w in ["daily", "today", "morning", "give", "show", "my", "get"])
        )

        if not is_briefing:
            return None

        # 1. Fetch user name & timestamp
        user_name = "User"
        if self.brain and hasattr(self.brain, "memory"):
            user_name = self.brain.memory.get("user", "name", user_id=user_id) or "User"
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%I:%M %p")

        # 2. Fetch Tasks
        tasks = db.get_user_tasks(user_id)
        pending_tasks = [t for t in tasks if not t.get("completed")]
        completed_tasks = [t for t in tasks if t.get("completed")]

        # 3. Fetch Projects
        projects = db.get_user_projects(user_id)

        # 4. Fetch Live News
        news_section = ""
        try:
            if self.brain and hasattr(self.brain, "search_engine"):
                news_data = self.brain.search_engine.fetch_live_news("top technology world news")
                if news_data:
                    news_lines = [line.strip() for line in news_data.split("\n") if line.strip() and not line.startswith("=")]
                    if news_lines:
                        top_headlines = news_lines[:3]
                        news_section = "\n\n**Latest Headlines:**\n" + "\n".join(f"- {h}" for h in top_headlines)
        except Exception:
            pass

        # 5. Build Briefing Document
        lines = [
            f"# Daily Briefing for {user_name}",
            f"**Date**: {date_str} | **Time**: {time_str}\n",
            f"## Task Checklist Overview",
            f"- **Pending Tasks**: {len(pending_tasks)} item(s)",
            f"- **Completed Tasks**: {len(completed_tasks)} item(s)",
        ]

        if pending_tasks:
            lines.append("\n**Top Priorities for Today:**")
            for t in pending_tasks[:5]:
                tag = f" `[{t.get('tag', 'General')}]`" if t.get('tag') else ""
                lines.append(f"- ○ **{t['title']}**{tag}")
        else:
            lines.append("\n*All tasks are checked off. No pending tasks for today.*")

        if projects:
            lines.append(f"\n## Active Projects Workspace ({len(projects)} total)")
            for p in projects[:3]:
                desc = p.get('description', '')
                snippet = f" — {desc[:80]}..." if desc and len(desc) > 80 else (f" — {desc}" if desc else "")
                lines.append(f"- **{p['name']}**{snippet}")

        if news_section:
            lines.append(news_section)

        lines.append("\nHave a focused and productive day.")

        return "\n".join(lines)
