import os
import tempfile
import unittest
from src.db import Database
from src import auth
from src.brain import Brain
from src.memory import MemoryManager


class UserIsolationTests(unittest.TestCase):

    def setUp(self):
        # Create a temporary database for test isolation
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()

        # Patch db singleton to use test database
        auth.db = Database(self.db_path)
        self.brain = Brain()
        self.brain.memory = MemoryManager()

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_user_registration_and_login(self):
        # Test valid registration
        user, err = auth.register_user("arun@example.com", "secret123", "Arun")
        self.assertIsNone(err)
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "arun@example.com")
        self.assertEqual(user["name"], "Arun")

        # Test duplicate registration
        dup_user, dup_err = auth.register_user("arun@example.com", "password123", "Arun 2")
        self.assertIsNotNone(dup_err)
        self.assertIsNone(dup_user)

        # Test login with valid credentials
        logged_in, login_err = auth.login_user("arun@example.com", "secret123")
        self.assertIsNone(login_err)
        self.assertEqual(logged_in["id"], user["id"])

        # Test login with invalid password
        bad_user, bad_err = auth.login_user("arun@example.com", "wrongpass")
        self.assertIsNotNone(bad_err)
        self.assertIsNone(bad_user)

    def test_session_creation_validation_logout(self):
        user, _ = auth.register_user("test@example.com", "password123", "Test User")
        session_id = auth.create_session(user["id"])
        self.assertIsNotNone(session_id)

        session = auth.validate_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session["user_id"], user["id"])

        # Test logout
        auth.logout_session(session_id)
        expired_session = auth.validate_session(session_id)
        self.assertIsNone(expired_session)

    def test_user_data_and_memory_isolation(self):
        # Create User A (Arun)
        user_a, _ = auth.register_user("arun@example.com", "pass12345", "Arun")
        user_id_a = user_a["id"]

        # Create User B (Priya)
        user_b, _ = auth.register_user("priya@example.com", "pass12345", "Priya")
        user_id_b = user_b["id"]

        # Save private memory for User A
        auth.db.set_memory(user_id_a, "personal", "favorite_color", "Blue")

        # Save private memory for User B
        auth.db.set_memory(user_id_b, "personal", "favorite_color", "Red")

        # Retrieve User A memory
        mem_a = auth.db.get_memory(user_id_a, "personal", "favorite_color")
        self.assertEqual(mem_a, "Blue")

        # Retrieve User B memory
        mem_b = auth.db.get_memory(user_id_b, "personal", "favorite_color")
        self.assertEqual(mem_b, "Red")

        # Ensure User A cannot access User B memory
        all_mem_a = auth.db.get_user_memories(user_id_a)
        all_mem_b = auth.db.get_user_memories(user_id_b)

        self.assertIn("favorite_color", all_mem_a["personal"])
        self.assertEqual(all_mem_a["personal"]["favorite_color"], "Blue")
        self.assertNotIn("Red", str(all_mem_a))

        self.assertIn("favorite_color", all_mem_b["personal"])
        self.assertEqual(all_mem_b["personal"]["favorite_color"], "Red")
        self.assertNotIn("Blue", str(all_mem_b))

    def test_brain_user_identity_vs_novax_creator_identity(self):
        user_a, _ = auth.register_user("arun@example.com", "pass12345", "Arun")
        user_id_a = user_a["id"]

        # Test Intent Manager handling name memory query
        intent_reply = self.brain.intent.process("remember my name is Arun", user_id=user_id_a)
        # Verify stored memory
        name_mem = auth.db.get_memory(user_id_a, "user", "name")
        self.assertEqual(name_mem, "Arun")

    def test_weather_intent_link_generation(self):
        user_a, _ = auth.register_user("arun@example.com", "pass12345", "Arun")
        user_id_a = user_a["id"]

        # User asks for weather at Trichy
        self.brain.conversation.add_user_message("i want to know the weather at trichy", user_id=user_id_a)

        # User asks for weather link
        reply = self.brain.intent.process("can you give me the link of the weather", user_id=user_id_a)
        self.assertIsNotNone(reply)
        self.assertIn("Trichy", reply)
        self.assertIn("https://www.google.com/search?q=weather+in+Trichy", reply)


if __name__ == "__main__":
    unittest.main()
