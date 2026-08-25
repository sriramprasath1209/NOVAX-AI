from src.db import db


class MemoryManager:

    def __init__(self):
        pass

    def load_memory(self, user_id="default_user"):
        return db.get_user_memories(user_id)

    def get(self, category, key, user_id="default_user"):
        return db.get_memory(user_id, category, key)

    def set(self, category, key, value, user_id="default_user"):
        db.set_memory(user_id, category, key, value)

    def delete(self, category, key, user_id="default_user"):
        db.delete_memory(user_id, category, key)