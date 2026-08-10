from src.chat import Chat
from src.web_app import run_server


class Assistant:

    def __init__(self, mode="cli"):
        self.chat = Chat()
        self.mode = mode

    def start(self):
        if self.mode == "web":
            run_server()
            return

        print("=" * 40)
        print("       Welcome to NOVAX-AI")
        print("=" * 40)

        self.chat.start_chat()