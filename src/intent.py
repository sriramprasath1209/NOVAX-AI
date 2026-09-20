from src.intents.memory_intent import MemoryIntent
from src.intents.task_intent import TaskIntent
from src.intents.project_intent import ProjectIntent
from src.intents.briefing_intent import BriefingIntent
from src.intents.weather_intent import WeatherIntent


class IntentManager:

    def __init__(self, brain=None):
        self.brain = brain

        # Register all intents here
        self.briefing_intent = BriefingIntent(brain)
        self.task_intent = TaskIntent(brain)
        self.project_intent = ProjectIntent(brain)
        self.memory_intent = MemoryIntent(brain)
        self.weather_intent = WeatherIntent(brain)

    def process(self, user_message, user_id="default_user"):
        # 1. Check Daily Briefing Intent
        response = self.briefing_intent.process(user_message, user_id=user_id)
        if response is not None:
            return response

        # 2. Check Task Checklist Intent
        response = self.task_intent.process(user_message, user_id=user_id)
        if response is not None:
            return response

        # 3. Check Project Workspace Intent
        response = self.project_intent.process(user_message, user_id=user_id)
        if response is not None:
            return response

        # 4. Check Memory Intent
        response = self.memory_intent.process(user_message, user_id=user_id)
        if response is not None:
            return response

        # 5. Check Weather Intent
        response = self.weather_intent.process(user_message, user_id=user_id)
        if response is not None:
            return response

        # No intent matched
        return None