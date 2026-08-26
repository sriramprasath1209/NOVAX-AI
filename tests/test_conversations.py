import os
import tempfile
import unittest
from src.db import Database
from src import auth
from src.brain import Brain
from src.memory import MemoryManager


class ConversationTests(unittest.TestCase):

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()

        test_db = Database(self.db_path)
        auth.db = test_db
        import src.db
        import src.brain
        import src.conversation
        src.db.db = test_db
        src.brain.db = test_db
        src.conversation.db = test_db

        self.brain = Brain()
        self.brain.ai.ask = lambda msgs: "Mocked AI response for testing."
        self.brain.memory = MemoryManager()

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_new_chat_and_auto_title_generation(self):
        user, _ = auth.register_user("testuser@example.com", "pass12345", "Test User")
        user_id = user["id"]

        conv_id_1 = "conv_test_1"
        reply1 = self.brain.get_response("Explain quantum computing in simple terms", user_id=user_id, user_name="Test User", conversation_id=conv_id_1)
        self.assertIsNotNone(reply1)

        conv1 = auth.db.get_conversation(conv_id_1, user_id)
        self.assertIsNotNone(conv1)
        self.assertIn("Explain quantum computing", conv1["title"])

        messages1 = auth.db.get_conversation_messages(conv_id_1, user_id)
        self.assertGreaterEqual(len(messages1), 2)
        self.assertEqual(messages1[0]["role"], "user")
        self.assertEqual(messages1[0]["content"], "Explain quantum computing in simple terms")

    def test_multiple_conversations_switching(self):
        user, _ = auth.register_user("arun@example.com", "pass12345", "Arun")
        user_id = user["id"]

        # Chat 1
        conv_1 = "conv_111"
        self.brain.get_response("Hello, what is Python?", user_id=user_id, user_name="Arun", conversation_id=conv_1)

        # Chat 2 (New Chat)
        conv_2 = "conv_222"
        self.brain.get_response("What is the weather in Trichy?", user_id=user_id, user_name="Arun", conversation_id=conv_2)

        # Fetch all user conversations
        user_convs = auth.db.get_user_conversations(user_id)
        self.assertEqual(len(user_convs), 2)
        titles = [c["title"] for c in user_convs]
        self.assertTrue(any("Python" in t for t in titles))
        self.assertTrue(any("Weather" in t or "Trichy" in t for t in titles))

        # Check messages of Conv 1 vs Conv 2
        msgs_1 = auth.db.get_conversation_messages(conv_1, user_id)
        msgs_2 = auth.db.get_conversation_messages(conv_2, user_id)

        self.assertEqual(msgs_1[0]["content"], "Hello, what is Python?")
        self.assertEqual(msgs_2[0]["content"], "What is the weather in Trichy?")

    def test_conversation_rename_and_deletion(self):
        user, _ = auth.register_user("user1@example.com", "pass12345", "User One")
        user_id = user["id"]

        conv_id = "conv_to_delete"
        self.brain.get_response("First message here", user_id=user_id, user_name="User One", conversation_id=conv_id)

        # Rename title
        auth.db.update_conversation_title(conv_id, user_id, "Custom Title")
        conv = auth.db.get_conversation(conv_id, user_id)
        self.assertEqual(conv["title"], "Custom Title")

        # Delete message
        msgs = auth.db.get_conversation_messages(conv_id, user_id)
        msg_id_to_del = msgs[0]["id"]
        auth.db.delete_message(msg_id_to_del, user_id)

        msgs_after = auth.db.get_conversation_messages(conv_id, user_id)
        self.assertEqual(len(msgs_after), len(msgs) - 1)

        # Delete conversation
        auth.db.delete_user_conversation(conv_id, user_id)
        conv_deleted = auth.db.get_conversation(conv_id, user_id)
        self.assertIsNone(conv_deleted)
        self.assertEqual(len(auth.db.get_conversation_messages(conv_id, user_id)), 0)

    def test_user_isolation_for_conversations(self):
        user_a, _ = auth.register_user("user_a@example.com", "pass12345", "User A")
        user_b, _ = auth.register_user("user_b@example.com", "pass12345", "User B")

        conv_a = "conv_user_a"
        conv_b = "conv_user_b"

        self.brain.get_response("User A secret topic", user_id=user_a["id"], user_name="User A", conversation_id=conv_a)
        self.brain.get_response("User B secret topic", user_id=user_b["id"], user_name="User B", conversation_id=conv_b)

        # User A cannot read User B's conversation
        msgs_b_from_a = auth.db.get_conversation_messages(conv_b, user_a["id"])
        self.assertEqual(len(msgs_b_from_a), 0)

        convs_a = auth.db.get_user_conversations(user_a["id"])
        conv_ids_a = [c["id"] for c in convs_a]
        self.assertIn(conv_a, conv_ids_a)
        self.assertNotIn(conv_b, conv_ids_a)


if __name__ == "__main__":
    unittest.main()
