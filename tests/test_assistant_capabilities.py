import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.db import Database
from src import auth
from src.intents.task_intent import TaskIntent
from src.intents.project_intent import ProjectIntent
from src.intents.briefing_intent import BriefingIntent
from src.intents.weather_intent import WeatherIntent
from src.intent import IntentManager


class AssistantCapabilitiesTests(unittest.TestCase):

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()

        self.test_db = Database(self.db_path)
        auth.db = self.test_db

        # Patch db module references in intents
        self.db_patcher = patch("src.intents.task_intent.db", self.test_db)
        self.db_patcher.start()

        self.db_proj_patcher = patch("src.intents.project_intent.db", self.test_db)
        self.db_proj_patcher.start()

        self.db_brief_patcher = patch("src.intents.briefing_intent.db", self.test_db)
        self.db_brief_patcher.start()

        # Create two test users
        self.user_a, _ = auth.register_user("alex@novax.ai", "pass12345", "Alex Morgan")
        self.user_b, _ = auth.register_user("taylor@novax.ai", "pass12345", "Taylor Swift")

        self.intent_manager = IntentManager()

    def tearDown(self):
        self.db_patcher.stop()
        self.db_proj_patcher.stop()
        self.db_brief_patcher.stop()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_task_intent_create(self):
        task_intent = TaskIntent()

        # Test direct command with tag
        resp = task_intent.process("add task Deploy neural cluster under Infrastructure", user_id=self.user_a["id"])
        self.assertIsNotNone(resp)
        self.assertIn("Task added to your Checklist", resp)
        self.assertIn("Deploy neural cluster", resp)
        self.assertIn("Infrastructure", resp)

        # Verify task is in DB
        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["title"], "Deploy neural cluster")
        self.assertEqual(tasks[0]["tag"], "Infrastructure")
        self.assertEqual(tasks[0]["completed"], 0)

    def test_task_intent_remind_me(self):
        task_intent = TaskIntent()
        resp = task_intent.process("remind me to Finish quarterly review", user_id=self.user_a["id"])
        self.assertIsNotNone(resp)
        self.assertIn("Task added to your Checklist", resp)
        self.assertIn("Finish quarterly review", resp)

        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["title"], "Finish quarterly review")

    def test_task_intent_list_and_complete(self):
        task_intent = TaskIntent()
        self.test_db.create_task("t1", self.user_a["id"], "Review pull requests", "Engineering")
        self.test_db.create_task("t2", self.user_a["id"], "Update architecture documentation", "Docs")

        # List tasks
        list_resp = task_intent.process("show my tasks", user_id=self.user_a["id"])
        self.assertIsNotNone(list_resp)
        self.assertIn("Your Task Checklist", list_resp)
        self.assertIn("Review pull requests", list_resp)
        self.assertIn("Update architecture documentation", list_resp)

        # Complete task
        comp_resp = task_intent.process("complete task Review pull requests", user_id=self.user_a["id"])
        self.assertIsNotNone(comp_resp)
        self.assertIn("Marked task", comp_resp)
        self.assertIn("Review pull requests", comp_resp)

        # Verify completion status in DB
        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        t1_item = next(t for t in tasks if t["id"] == "t1")
        self.assertEqual(t1_item["completed"], 1)

    def test_project_intent_create_and_list(self):
        proj_intent = ProjectIntent()
        resp = proj_intent.process("create project AI Agent Workspace with description Personal autonomous assistant", user_id=self.user_a["id"])
        self.assertIsNotNone(resp)
        self.assertIn("Project created in your Projects Workspace", resp)
        self.assertIn("AI Agent Workspace", resp)

        projects = self.test_db.get_user_projects(self.user_a["id"])
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["name"], "AI Agent Workspace")

        # List projects
        list_resp = proj_intent.process("list my projects", user_id=self.user_a["id"])
        self.assertIsNotNone(list_resp)
        self.assertIn("Your Projects Workspace", list_resp)
        self.assertIn("AI Agent Workspace", list_resp)

    def test_briefing_intent(self):
        briefing_intent = BriefingIntent()

        # Seed some tasks and projects
        self.test_db.create_task("t1", self.user_a["id"], "Submit budget forecast", "Finance")
        self.test_db.create_task("t2", self.user_a["id"], "Plan sprint goals", "Planning")
        self.test_db.create_project("p1", self.user_a["id"], "NOVAX Assistant 2.0", "Next gen assistant")

        # Test briefing generation
        resp = briefing_intent.process("give me my daily briefing", user_id=self.user_a["id"])
        self.assertIsNotNone(resp)
        self.assertIn("Daily Briefing", resp)
        self.assertIn("Submit budget forecast", resp)
        self.assertIn("NOVAX Assistant 2.0", resp)
        self.assertIn("Pending Tasks", resp)

    @patch("urllib.request.urlopen")
    def test_weather_intent_with_mock_api(self, mock_urlopen):
        # Mock weather response JSON from wttr.in
        fake_weather_json = b'''{
            "current_condition": [
                {
                    "temp_C": "26",
                    "temp_F": "79",
                    "weatherDesc": [{"value": "Sunny"}],
                    "humidity": "45",
                    "FeelsLikeC": "27",
                    "windspeedKmph": "12"
                }
            ],
            "nearest_area": [
                {
                    "areaName": [{"value": "San Francisco"}],
                    "country": [{"value": "United States"}]
                }
            ]
        }'''
        mock_response = MagicMock()
        mock_response.read.return_value = fake_weather_json
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        weather_intent = WeatherIntent()
        resp = weather_intent.process("weather in San Francisco", user_id=self.user_a["id"])
        self.assertIsNotNone(resp)
        self.assertIn("Live Weather Report", resp)
        self.assertIn("San Francisco", resp)
        self.assertIn("26", resp)
        self.assertIn("Sunny", resp)

    def test_intent_manager_routing(self):
        # Verify routing through IntentManager
        resp = self.intent_manager.process("add task Write end-to-end tests", user_id=self.user_a["id"])
        self.assertIsNotNone(resp)
        self.assertIn("Task added to your Checklist", resp)
        self.assertIn("Write end-to-end tests", resp)


if __name__ == "__main__":
    unittest.main()
