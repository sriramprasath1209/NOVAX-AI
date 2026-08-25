from src.intents.memory_intent import MemoryIntent
from src.intents.weather_intent import WeatherIntent


class IntentManager:

    def __init__(self, brain):

        self.brain = brain

        # Register all intents here
        self.memory_intent = MemoryIntent(brain)
        self.weather_intent = WeatherIntent(brain)

    def process(self, user_message, user_id="default_user"):

        # Check Memory Intent
        response = self.memory_intent.process(user_message, user_id=user_id)
        if response is not None:
            return response

        # Check Weather Intent
        response = self.weather_intent.process(user_message, user_id=user_id)
        if response is not None:
            return response

        # No intent matched
        return None