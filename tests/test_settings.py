import os
import tempfile
import unittest
from unittest.mock import MagicMock
from src.db import Database
from src import auth
from src.brain import Brain


class SettingsModuleTests(unittest.TestCase):

    def setUp(self):
        # Create a temporary database for test isolation
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()

        self.test_db = Database(self.db_path)
        auth.db = self.test_db
        import src.db
        import src.brain
        import src.memory
        import src.conversation
        src.db.db = self.test_db
        src.brain.db = self.test_db
        src.memory.db = self.test_db
        src.conversation.db = self.test_db

        self.user_a, _ = auth.register_user("user_a@novax.ai", "pass12345", "Alice")
        self.user_b, _ = auth.register_user("user_b@novax.ai", "pass12345", "Bob")

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_default_settings(self):
        settings = self.test_db.get_user_settings(self.user_a["id"])
        self.assertEqual(settings["response_style"], "default")
        self.assertTrue(settings["web_search"])
        self.assertEqual(settings["theme"], "dark")
        self.assertEqual(settings["font_size"], "normal")

    def test_update_settings(self):
        updated = self.test_db.update_user_settings(
            self.user_a["id"],
            response_style="concise",
            web_search=False,
            theme="midnight",
            font_size="large"
        )
        self.assertEqual(updated["response_style"], "concise")
        self.assertFalse(updated["web_search"])
        self.assertEqual(updated["theme"], "midnight")
        self.assertEqual(updated["font_size"], "large")

        # Verify retrieval matches
        fetched = self.test_db.get_user_settings(self.user_a["id"])
        self.assertEqual(fetched["response_style"], "concise")
        self.assertFalse(fetched["web_search"])
        self.assertEqual(fetched["theme"], "midnight")
        self.assertEqual(fetched["font_size"], "large")

    def test_settings_user_isolation(self):
        self.test_db.update_user_settings(self.user_a["id"], response_style="code_first", theme="oled")
        self.test_db.update_user_settings(self.user_b["id"], response_style="in_depth", theme="midnight")

        settings_a = self.test_db.get_user_settings(self.user_a["id"])
        settings_b = self.test_db.get_user_settings(self.user_b["id"])

        self.assertEqual(settings_a["response_style"], "code_first")
        self.assertEqual(settings_a["theme"], "oled")

        self.assertEqual(settings_b["response_style"], "in_depth")
        self.assertEqual(settings_b["theme"], "midnight")

    def test_update_user_profile(self):
        self.test_db.update_user_profile(self.user_a["id"], name="Alice Wonderland")
        logged_in, err = auth.login_user("user_a@novax.ai", "pass12345")
        self.assertIsNone(err)
        self.assertEqual(logged_in["name"], "Alice Wonderland")

        # Test updating password
        new_hash, salt = auth.hash_password("newsecret999")
        self.test_db.update_user_profile(self.user_a["id"], password_hash=new_hash, salt=salt)
        old_login, old_err = auth.login_user("user_a@novax.ai", "pass12345")
        self.assertIsNotNone(old_err)
        new_login, new_err = auth.login_user("user_a@novax.ai", "newsecret999")
        self.assertIsNone(new_err)
        self.assertIsNotNone(new_login)

    def test_export_and_clear_workspace(self):
        # Add tasks and projects
        self.test_db.create_task("t1", self.user_a["id"], "Task 1")
        self.test_db.create_project("p1", self.user_a["id"], "Project 1")
        self.test_db.set_memory(self.user_a["id"], "personal", "hobby", "Gaming")

        export_data = self.test_db.export_user_data(self.user_a["id"])
        self.assertIn("profile", export_data)
        self.assertIn("settings", export_data)
        self.assertEqual(len(export_data["tasks"]), 1)
        self.assertEqual(len(export_data["projects"]), 1)
        self.assertIn("personal", export_data["memories"])

        # Clear workspace
        self.test_db.clear_user_workspace(self.user_a["id"])
        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        projects = self.test_db.get_user_projects(self.user_a["id"])
        memories = self.test_db.get_user_memories(self.user_a["id"])

        self.assertEqual(len(tasks), 0)
        self.assertEqual(len(projects), 0)
        self.assertEqual(len(memories), 0)

    def test_brain_dynamic_settings_prompt(self):
        brain = Brain()
        brain.ai.ask = MagicMock(return_value="Mocked AI response")

        # Set user settings to concise
        self.test_db.update_user_settings(self.user_a["id"], response_style="concise", web_search=False)
        brain.get_response("Hello NOVAX", user_id=self.user_a["id"], user_name="Alice")

        # Inspect sent messages to AI
        call_args = brain.ai.ask.call_args[0][0]
        sys_msg = [m for m in call_args if m.get("role") == "system" and "Current User Name" in m.get("content", "")]
        self.assertTrue(len(sys_msg) > 0)
        self.assertIn("[Active Response Style: CONCISE]", sys_msg[0]["content"])

        # Change user settings to code_first
        self.test_db.update_user_settings(self.user_a["id"], response_style="code_first")
        brain.get_response("Show me quicksort", user_id=self.user_a["id"], user_name="Alice")

        call_args_2 = brain.ai.ask.call_args[0][0]
        sys_msg_2 = [m for m in call_args_2 if m.get("role") == "system" and "Current User Name" in m.get("content", "")]
        self.assertIn("[Active Response Style: CODE-FIRST]", sys_msg_2[0]["content"])


if __name__ == "__main__":
    unittest.main()
