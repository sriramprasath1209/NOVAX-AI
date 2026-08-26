import sqlite3
import os
import time
import json
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "novax.db"
OLD_MEMORY_PATH = Path(__file__).resolve().parent.parent / "data" / "memory.json"

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
                       MAX(m.created_at) as last_message_at
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

    def delete_project(self, project_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
            conn.commit()

    # --- Tasks queries ---
    def get_user_tasks(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def create_task(self, task_id, user_id, title, tag="User Task"):
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

    def delete_task(self, task_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
            conn.commit()

db = Database()
