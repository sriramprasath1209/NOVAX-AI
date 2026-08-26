import os
import unittest
from unittest.mock import MagicMock
from src.db import Database
from src.memory import MemoryManager
from src.brain import Brain
from src.intents.memory_intent import MemoryIntent


class TestMemoryCenter(unittest.TestCase):

    def setUp(self):
        self.db_path = "data/test_memory_center.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.db = Database(db_path=self.db_path)
        self.memory = MemoryManager()
        
        # Patch db singletons
        import src.db
        import src.memory
        import src.auth
        import src.brain
        src.db.db = self.db
        src.memory.db = self.db
        src.auth.db = self.db
        src.brain.db = self.db

        import uuid
        uid = str(uuid.uuid4())[:8]
        email_a = f"user_a_{uid}@example.com"
        email_b = f"user_b_{uid}@example.com"

        self.user_a_id = f"user_a_{uid}"
        self.user_b_id = f"user_b_{uid}"
        # Create test users (user_id, email, name)
        self.db.create_user(self.user_a_id, email_a, "Arun")
        self.db.create_user(self.user_b_id, email_b, "Priya")

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_memory_crud_operations(self):
        # Create
        self.memory.set("profile", "country", "India", user_id=self.user_a_id, source="USER")
        self.memory.set("career", "tech_skills", "Python, Git", user_id=self.user_a_id, source="USER")

        # Read
        val = self.memory.get("profile", "country", user_id=self.user_a_id)
        self.assertEqual(val, "India")

        memories = self.memory.load_memory(user_id=self.user_a_id)
        self.assertIn("profile", memories)
        self.assertEqual(memories["profile"]["country"]["value"], "India")
        self.assertEqual(memories["profile"]["country"]["source"], "USER")

        # Update
        self.memory.set("profile", "country", "Germany", user_id=self.user_a_id, source="USER")
        self.assertEqual(self.memory.get("profile", "country", user_id=self.user_a_id), "Germany")

        # Delete
        self.memory.delete("profile", "country", user_id=self.user_a_id)
        self.assertIsNone(self.memory.get("profile", "country", user_id=self.user_a_id))

    def test_search_and_clear_all(self):
        self.memory.set("skills", "programming_language", "Python", user_id=self.user_a_id)
        self.memory.set("goals", "learning", "Master Data Structures", user_id=self.user_a_id)

        # Search
        results = self.memory.search("Python", user_id=self.user_a_id)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["key"], "programming_language")

        # Clear All
        self.memory.clear_all(user_id=self.user_a_id)
        memories = self.memory.load_memory(user_id=self.user_a_id)
        self.assertEqual(len(memories), 0)

    def test_strict_user_isolation(self):
        # User A setup
        self.memory.set("profile", "name", "Arun", user_id=self.user_a_id)
        self.memory.set("career", "skill", "Python", user_id=self.user_a_id)

        # User B setup
        self.memory.set("profile", "name", "Priya", user_id=self.user_b_id)
        self.memory.set("career", "skill", "Java", user_id=self.user_b_id)

        # Verify User A only sees User A data
        mem_a = self.memory.load_memory(user_id=self.user_a_id)
        self.assertEqual(mem_a["profile"]["name"]["value"], "Arun")
        self.assertEqual(mem_a["career"]["skill"]["value"], "Python")
        self.assertNotIn("Priya", str(mem_a))
        self.assertNotIn("Java", str(mem_a))

        # Verify User B only sees User B data
        mem_b = self.memory.load_memory(user_id=self.user_b_id)
        self.assertEqual(mem_b["profile"]["name"]["value"], "Priya")
        self.assertEqual(mem_b["career"]["skill"]["value"], "Java")
        self.assertNotIn("Arun", str(mem_b))
        self.assertNotIn("Python", str(mem_b))

    def test_explicit_memory_commands(self):
        brain_mock = MagicMock()
        brain_mock.memory = self.memory
        intent = MemoryIntent(brain_mock)

        # "Remember my name is Arun"
        res1 = intent.process("remember my name is Arun", user_id=self.user_a_id)
        self.assertIn("Arun", res1)
        self.assertEqual(self.memory.get("profile", "name", user_id=self.user_a_id), "Arun")

        # "Remember that programming language is Python"
        res2 = intent.process("remember that programming language is Python", user_id=self.user_a_id)
        self.assertIn("saved", res2.lower())

        # "Show me what you remember"
        res3 = intent.process("show me what you remember", user_id=self.user_a_id)
        self.assertIn("Arun", res3)
        self.assertIn("Python", res3)

        # "Forget my name"
        res4 = intent.process("forget my name", user_id=self.user_a_id)
        self.assertIn("forgotten", res4.lower())
        self.assertIsNone(self.memory.get("profile", "name", user_id=self.user_a_id))

        # "Delete all my memories"
        res5 = intent.process("delete all my memories", user_id=self.user_a_id)
        self.assertIn("cleared", res5.lower())
        self.assertEqual(len(self.memory.load_memory(user_id=self.user_a_id)), 0)


if __name__ == "__main__":
    unittest.main()
