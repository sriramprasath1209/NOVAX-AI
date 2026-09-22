import os
import sys
from pathlib import Path

# Add project root directory to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure Vercel environment flag
os.environ.setdefault("VERCEL", "1")

# Load environment configuration
import src.config
from src.web_app import NOVAXRequestHandler, wsgi_app
import json

def debug_app(environ, start_response):
    # Unconditionally dump environ for inspection if PATH_INFO contains debug or query string contains debug or header has x-debug
    qs = environ.get("QUERY_STRING", "")
    path = environ.get("PATH_INFO", "")
    if "debug" in qs or "debug" in path or environ.get("HTTP_X_DEBUG") == "1":
        headers = {k: str(v) for k, v in environ.items() if "KEY" not in k and "SECRET" not in k and not k.startswith("wsgi.")}
        body = json.dumps({"environ": headers, "PATH_INFO": path, "QUERY_STRING": qs}, indent=2).encode("utf-8")
        start_response("200 OK", [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))])
        return [body]
    return wsgi_app(environ, start_response)


# Export the standard WSGI app and handler for Vercel Serverless Functions
app = debug_app
handler = debug_app

