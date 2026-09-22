import os
import sys
from pathlib import Path

# Add project root directory to Python path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import src.config
from src.assistant import Assistant
from src.web_app import NOVAXRequestHandler, wsgi_app

# Export standard WSGI app and handler for Vercel / serverless runtime
app = wsgi_app
handler = NOVAXRequestHandler


if __name__ == "__main__":
    mode = "web" if len(sys.argv) > 1 and sys.argv[1] == "web" else "cli"
    assistant = Assistant(mode=mode)
    assistant.start()
