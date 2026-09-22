import sqlite3
import os
import time
import json
from pathlib import Path
from contextlib import contextmanager

_default_db_dir = Path(__file__).resolve().parent.parent / "data"
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    _default_db_path = Path("/tmp/novax.db")
else:
    _default_db_path = _default_db_dir / "novax.db"

DB_PATH = Path(os.environ.get("DB_PATH", os.environ.get("NOVAX_DB_PATH", str(_default_db_path))))
OLD_MEMORY_PATH = _default_db_dir / "memory.json"

class MemoryValue(str):
    def __new__(cls, value, source="USER", created_at=0, updated_at=0):
        val_str = str(value) if value is not None else ""
        obj = super().__new__(cls, val_str)
        obj.value = val_str
        obj.source = source
        obj.created_at = created_at
        obj.updated_at = updated_at
        return obj

    def get(self, key, default=None):
        if key == "value": return self.value
        if key == "source": return self.source
        if key == "created_at": return self.created_at
        if key == "updated_at": return self.updated_at
        return default

    def __getitem__(self, item):
        if item == "value": return self.value
        if item == "source": return self.source
        if item == "created_at": return self.created_at
        if item == "updated_at": return self.updated_at
        return super().__getitem__(item)

class Database:
    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    salt TEXT,
                    name TEXT NOT NULL,
                    google_id TEXT UNIQUE,
                    created_at REAL NOT NULL
                )
            """)

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Memories table (user isolated)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    source TEXT DEFAULT 'USER',
                    created_at REAL DEFAULT 0,
                    updated_at REAL NOT NULL,
                    UNIQUE(user_id, category, key),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Dynamic column migration for existing databases
            cursor.execute("PRAGMA table_info(memories)")
            columns = [col[1] for col in cursor.fetchall()]
            if "source" not in columns:
                cursor.execute("ALTER TABLE memories ADD COLUMN source TEXT DEFAULT 'USER'")
            if "created_at" not in columns:
                cursor.execute("ALTER TABLE memories ADD COLUMN created_at REAL DEFAULT 0")

            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    completed INTEGER DEFAULT 0,
                    tag TEXT DEFAULT 'User Task',
                    created_at REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    user_id TEXT PRIMARY KEY,
                    response_style TEXT DEFAULT 'default',
                    web_search INTEGER DEFAULT 1,
                    theme TEXT DEFAULT 'dark',
                    font_size TEXT DEFAULT 'normal',
                    updated_at REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            conn.commit()

        # Migrate old data/memory.json into fallback admin if needed
        self._migrate_old_memory()

    def _migrate_old_memory(self):
        if OLD_MEMORY_PATH.exists():
            try:
                with open(OLD_MEMORY_PATH, "r") as f:
                    old_mem = json.load(f)
                if old_mem:
                    default_user_id = "default_user"
                    with self.get_connection() as conn:
                        cursor = conn.cursor()
                        # Ensure default user exists
                        cursor.execute("""
                            INSERT OR IGNORE INTO users (id, email, name, created_at)
                            VALUES (?, ?, ?, ?)
                        """, (default_user_id, "default@novax.ai", "Default User", time.time()))

                        for cat, items in old_mem.items():
                            if isinstance(items, dict):
                                for k, v in items.items():
                                    val_str = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                                    cursor.execute("""
                                        INSERT OR REPLACE INTO memories (user_id, category, key, value, updated_at)
                                        VALUES (?, ?, ?, ?, ?)
                                    """, (default_user_id, cat, k, val_str, time.time()))
                        conn.commit()
            except Exception:
                pass

    # --- User queries ---
    def create_user(self, user_id, email, name, password_hash=None, salt=None, google_id=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, salt, name, google_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, email.lower().strip(), password_hash, salt, name.strip(), google_id, time.time()))
            conn.commit()

    def get_user_by_email(self, email):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email.lower().strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_google_id(self, google_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE google_id = ?", (google_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # --- Session queries ---
    def create_session(self, session_id, user_id, expires_at):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            """, (session_id, user_id, time.time(), expires_at))
            conn.commit()

    def get_session(self, session_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.session_id, s.user_id, s.expires_at, u.id, u.email, u.name 
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_id = ? AND s.expires_at > ?
            """, (session_id, time.time()))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_session(self, session_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()

    # --- Memory queries ---
    def get_user_memories(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category, key, value, source, created_at, updated_at FROM memories WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))
            rows = cursor.fetchall()
            result = {}
            for row in rows:
                cat = row["category"]
                k = row["key"]
                v = row["value"]
                src = row["source"] or "USER"
                c_at = row["created_at"] or row["updated_at"]
                u_at = row["updated_at"]
                if cat not in result:
                    result[cat] = {}
                result[cat][k] = MemoryValue(v, source=src, created_at=c_at, updated_at=u_at)
            return result

    def get_memory(self, user_id, category, key):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM memories WHERE user_id = ? AND category = ? AND key = ?", (user_id, category, key))
            row = cursor.fetchone()
            return row["value"] if row else None

    def set_memory(self, user_id, category, key, value, source="USER"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = time.time()
            cursor.execute("SELECT created_at FROM memories WHERE user_id = ? AND category = ? AND key = ?", (user_id, category, key))
            existing = cursor.fetchone()
            created_at = existing["created_at"] if existing and existing["created_at"] else now

            cursor.execute("""
                INSERT OR REPLACE INTO memories (user_id, category, key, value, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, category, key, str(value), source, created_at, now))
            conn.commit()

    def delete_memory(self, user_id, category, key):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE user_id = ? AND category = ? AND key = ?", (user_id, category, key))
            conn.commit()

    def clear_user_memories(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
            conn.commit()

    def search_user_memories(self, user_id, query):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            q = f"%{query.strip().lower()}%"
            cursor.execute("""
                SELECT category, key, value, source, created_at, updated_at
                FROM memories
                WHERE user_id = ? AND (LOWER(key) LIKE ? OR LOWER(value) LIKE ? OR LOWER(category) LIKE ?)
                ORDER BY updated_at DESC
            """, (user_id, q, q, q))
            return [dict(row) for row in cursor.fetchall()]

    # --- Conversation queries ---
    def get_user_conversations(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.user_id, c.title, c.created_at,
                       COUNT(m.id) as message_count,
                       MAX(m.created_at) as last_message_at,
                       (SELECT content FROM messages WHERE conversation_id = c.id AND user_id = c.user_id ORDER BY created_at DESC LIMIT 1) as last_message
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id AND c.user_id = m.user_id
                WHERE c.user_id = ?
                GROUP BY c.id
                ORDER BY COALESCE(MAX(m.created_at), c.created_at) DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_conversation(self, conv_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_conversation(self, conv_id, user_id, title="New Chat"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO conversations (id, user_id, title, created_at)
                VALUES (?, ?, ?, ?)
            """, (conv_id, user_id, title, time.time()))
            conn.commit()

    def update_conversation_title(self, conv_id, user_id, title):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE conversations SET title = ? WHERE id = ? AND user_id = ?
            """, (title, conv_id, user_id))
            conn.commit()

    def add_message(self, conv_id, user_id, role, content):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (conversation_id, user_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (conv_id, user_id, role, content, time.time()))
            conn.commit()

    def get_conversation_messages(self, conv_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, conversation_id, user_id, role, content, created_at FROM messages
                WHERE conversation_id = ? AND user_id = ?
                ORDER BY id ASC
            """, (conv_id, user_id))
            return [dict(row) for row in cursor.fetchall()]

    def delete_message(self, message_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE id = ? AND user_id = ?", (message_id, user_id))
            conn.commit()

    def delete_user_conversation(self, conv_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE conversation_id = ? AND user_id = ?", (conv_id, user_id))
            cursor.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id))
            conn.commit()

    # --- Projects queries ---
    def get_user_projects(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def create_project(self, project_id, user_id, name, description=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (id, user_id, name, description, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (project_id, user_id, name, description, time.time()))
            conn.commit()

    def update_project(self, project_id, user_id, name, description=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE projects
                SET name = ?, description = ?
                WHERE id = ? AND user_id = ?
            """, (name, description, project_id, user_id))
            conn.commit()

    def delete_project(self, project_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
            conn.commit()

    # --- Tasks queries ---
    def get_user_tasks(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY completed ASC, created_at DESC", (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def create_task(self, task_id, user_id, title, tag="General"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (id, user_id, title, completed, tag, created_at)
                VALUES (?, ?, ?, 0, ?, ?)
            """, (task_id, user_id, title, tag, time.time()))
            conn.commit()

    def toggle_task(self, task_id, user_id, completed):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET completed = ? WHERE id = ? AND user_id = ?", (1 if completed else 0, task_id, user_id))
            conn.commit()

    def update_task(self, task_id, user_id, title, tag=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if tag is not None:
                cursor.execute("UPDATE tasks SET title = ?, tag = ? WHERE id = ? AND user_id = ?", (title, tag, task_id, user_id))
            else:
                cursor.execute("UPDATE tasks SET title = ? WHERE id = ? AND user_id = ?", (title, task_id, user_id))
            conn.commit()

    def delete_task(self, task_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
            conn.commit()

    def clear_completed_tasks(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE completed = 1 AND user_id = ?", (user_id,))
            conn.commit()

    # --- Settings & Profile queries ---
    def get_user_settings(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                return {
                    "response_style": d.get("response_style") or "default",
                    "web_search": bool(d.get("web_search", 1)),
                    "theme": d.get("theme") or "dark",
                    "font_size": d.get("font_size") or "normal",
                    "updated_at": d.get("updated_at", 0)
                }
            return {
                "response_style": "default",
                "web_search": True,
                "theme": "dark",
                "font_size": "normal",
                "updated_at": time.time()
            }

    def update_user_settings(self, user_id, response_style=None, web_search=None, theme=None, font_size=None):
        current = self.get_user_settings(user_id)
        new_style = response_style if response_style is not None else current["response_style"]
        new_search = int(web_search) if web_search is not None else (1 if current["web_search"] else 0)
        new_theme = theme if theme is not None else current["theme"]
        new_font = font_size if font_size is not None else current["font_size"]
        now = time.time()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (user_id, response_style, web_search, theme, font_size, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    response_style = excluded.response_style,
                    web_search = excluded.web_search,
                    theme = excluded.theme,
                    font_size = excluded.font_size,
                    updated_at = excluded.updated_at
            """, (user_id, new_style, new_search, new_theme, new_font, now))
            conn.commit()
        return self.get_user_settings(user_id)

    def update_user_profile(self, user_id, name=None, password_hash=None, salt=None):
        now = time.time()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if name is not None and password_hash is not None and salt is not None:
                cursor.execute("UPDATE users SET name = ?, password_hash = ?, salt = ? WHERE id = ?", (name, password_hash, salt, user_id))
                cursor.execute("""
                    INSERT OR REPLACE INTO memories (user_id, category, key, value, source, created_at, updated_at)
                    VALUES (?, 'user', 'name', ?, 'USER', ?, ?)
                """, (user_id, name, now, now))
            elif name is not None:
                cursor.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
                cursor.execute("""
                    INSERT OR REPLACE INTO memories (user_id, category, key, value, source, created_at, updated_at)
                    VALUES (?, 'user', 'name', ?, 'USER', ?, ?)
                """, (user_id, name, now, now))
            elif password_hash is not None and salt is not None:
                cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (password_hash, salt, user_id))
            conn.commit()

    def export_user_data(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, name, created_at FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            user_profile = dict(user_row) if user_row else {}

            settings = self.get_user_settings(user_id)
            memories = self.get_user_memories(user_id)

            cursor.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY created_at ASC", (user_id,))
            conv_rows = [dict(r) for r in cursor.fetchall()]
            conversations = []
            for conv in conv_rows:
                cursor.execute("SELECT role, content, created_at FROM messages WHERE conversation_id = ? AND user_id = ? ORDER BY id ASC", (conv["id"], user_id))
                conv["messages"] = [dict(m) for m in cursor.fetchall()]
                conversations.append(conv)

            projects = self.get_user_projects(user_id)
            tasks = self.get_user_tasks(user_id)

            return {
                "exported_at": time.time(),
                "profile": user_profile,
                "settings": settings,
                "memories": memories,
                "conversations": conversations,
                "projects": projects,
                "tasks": tasks
            }

    def clear_user_workspace(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM projects WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
            conn.commit()

db = Database()
