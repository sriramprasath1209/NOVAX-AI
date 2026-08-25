import src.config
from src.assistant import Assistant


if __name__ == "__main__":
    import sys

    mode = "web" if len(sys.argv) > 1 and sys.argv[1] == "web" else "cli"
    assistant = Assistant(mode=mode)
    assistant.start()
