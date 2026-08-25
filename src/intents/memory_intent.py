class MemoryIntent:

    def __init__(self, brain):
        self.brain = brain

    def process(self, user_message, user_id="default_user"):

        message = user_message.lower().strip()

        # Remember user's name
        if message.startswith("remember my name is"):

            name = user_message[len("remember my name is"):].strip()

            if not name:
                return "Please tell me the name you want me to remember."

            self.brain.memory.set(
                "user",
                "name",
                name,
                user_id=user_id
            )

            return f"I'll remember that your name is {name}."

        return None