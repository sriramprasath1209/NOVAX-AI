from src.brain import Brain


class Chat:

    def __init__(self):
        self.brain = Brain()

    def start_chat(self):

        while True:

            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                print("\nNOVAX-AI: Goodbye! Have a great day.")
                break

            response = self.brain.get_response(user_input)

            print(f"\nNOVAX-AI: {response}")