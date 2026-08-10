from src.intents.memory_intent import MemoryIntent


class IntentManager:

    def __init__(self, brain):

        self.brain = brain

        # Register all intents here
        self.memory_intent = MemoryIntent(brain)

    def process(self, user_message):

        # Check Memory Intent
        response = self.memory_intent.process(user_message)

        if response is not None:
            return response

        # No intent matched
        return None