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
from src.web_app import NOVAXRequestHandler

# Export the handler and app for Vercel Serverless Function
class handler(NOVAXRequestHandler):
    pass

app = handler
