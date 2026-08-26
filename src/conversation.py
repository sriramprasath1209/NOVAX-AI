import secrets
from src.db import db


class Conversation:

    def __init__(self):
        self.conversations_by_user = {}

    def get_user_messages(self, user_id="default_user", conversation_id=None):
        return self.get_messages(user_id=user_id, conversation_id=conversation_id)

    def add_user_message(self, message, user_id="default_user", conversation_id=None):
        if user_id not in self.conversations_by_user:
            self.conversations_by_user[user_id] = []
        msg = {"role": "user", "content": message}
        self.conversations_by_user[user_id].append(msg)
        if conversation_id:
            db.add_message(conversation_id, user_id, "user", message)

    def add_assistant_message(self, message, user_id="default_user", conversation_id=None):
        if user_id not in self.conversations_by_user:
            self.conversations_by_user[user_id] = []
        msg = {"role": "assistant", "content": message}
        self.conversations_by_user[user_id].append(msg)
        if conversation_id:
            db.add_message(conversation_id, user_id, "assistant", message)

    def get_messages(self, user_id="default_user", conversation_id=None):
        if conversation_id:
            db_msgs = db.get_conversation_messages(conversation_id, user_id)
            if db_msgs:
                return [{"role": m["role"], "content": m["content"]} for m in db_msgs]
        return self.conversations_by_user.get(user_id, [])

    def clear(self, user_id="default_user"):
        self.conversations_by_user[user_id] = []