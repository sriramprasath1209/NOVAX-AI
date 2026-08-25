import hashlib
import secrets
import time
import os
import urllib.parse
import urllib.request
import json
import src.config
from src.db import db

SESSION_DURATION = 7 * 24 * 60 * 60  # 7 days in seconds

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return hashed, salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    new_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(new_hash, password_hash)

def register_user(email: str, password: str, name: str) -> tuple[dict | None, str | None]:
    email = email.lower().strip()
    name = name.strip()

    if not email or "@" not in email:
        return None, "Please enter a valid email address."
    if not name:
        return None, "Please enter your name."
    if not password or len(password) < 6:
        return None, "Password must be at least 6 characters."

    existing = db.get_user_by_email(email)
    if existing:
        return None, "An account with this email already exists."

    user_id = secrets.token_hex(12)
    pwd_hash, salt = hash_password(password)

    try:
        db.create_user(user_id=user_id, email=email, name=name, password_hash=pwd_hash, salt=salt)
        # Store user name in user memory
        db.set_memory(user_id, "user", "name", name)
        user = db.get_user_by_id(user_id)
        return user, None
    except Exception as e:
        return None, "Unable to create account. Please try again."

def login_user(email: str, password: str) -> tuple[dict | None, str | None]:
    email = email.lower().strip()
    if not email or not password:
        return None, "Please enter both email and password."

    user = db.get_user_by_email(email)
    if not user or not user.get("password_hash") or not user.get("salt"):
        return None, "Invalid email or password."

    if not verify_password(password, user["password_hash"], user["salt"]):
        return None, "Invalid email or password."

    return user, None

def create_session(user_id: str) -> str:
    session_id = secrets.token_hex(32)
    expires_at = time.time() + SESSION_DURATION
    db.create_session(session_id, user_id, expires_at)
    return session_id

def validate_session(session_id: str) -> dict | None:
    if not session_id:
        return None
    return db.get_session(session_id)

def logout_session(session_id: str):
    if session_id:
        db.delete_session(session_id)

# --- Google OAuth Flow Helpers ---
def get_google_auth_url(redirect_uri: str) -> str:
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    if not client_id:
        return ""
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account"
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

def process_google_callback(code: str, redirect_uri: str) -> tuple[dict | None, str | None]:
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    
    if not client_id or not client_secret:
        return None, "Google OAuth is not configured on the server."

    try:
        # Exchange code for tokens
        token_data = urllib.parse.urlencode({
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }).encode("utf-8")

        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=token_data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        with urllib.request.urlopen(req) as resp:
            tokens = json.loads(resp.read().decode("utf-8"))

        access_token = tokens.get("access_token")
        if not access_token:
            return None, "Failed to retrieve access token from Google."

        # Fetch user info
        userinfo_req = urllib.request.Request("https://www.googleapis.com/oauth2/v3/userinfo")
        userinfo_req.add_header("Authorization", f"Bearer {access_token}")

        with urllib.request.urlopen(userinfo_req) as resp:
            user_info = json.loads(resp.read().decode("utf-8"))

        google_id = user_info.get("sub")
        email = user_info.get("email", "")
        name = user_info.get("name") or email.split("@")[0]

        if not google_id or not email:
            return None, "Invalid Google user response."

        # Check existing user by google_id or email
        user = db.get_user_by_google_id(google_id)
        if not user:
            user = db.get_user_by_email(email)

        if user:
            # Update user with google_id if missing
            if not user.get("google_id"):
                with db.get_connection() as conn:
                    conn.cursor().execute("UPDATE users SET google_id = ? WHERE id = ?", (google_id, user["id"]))
                    conn.commit()
                user = db.get_user_by_id(user["id"])
        else:
            # Register new Google user
            user_id = secrets.token_hex(12)
            db.create_user(user_id=user_id, email=email, name=name, google_id=google_id)
            db.set_memory(user_id, "user", "name", name)
            user = db.get_user_by_id(user_id)

        return user, None

    except Exception as e:
        return None, f"Google Authentication failed: {str(e)}"
