import os
import tempfile
import unittest
from src.db import Database
from src import auth


class TasksModuleTests(unittest.TestCase):

    def setUp(self):
        # Create a temporary database for test isolation
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()

        self.test_db = Database(self.db_path)
        auth.db = self.test_db

        # Create two test users
        self.user_a, _ = auth.register_user("user_a@novax.ai", "pass12345", "User A")
        self.user_b, _ = auth.register_user("user_b@novax.ai", "pass12345", "User B")

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_create_and_get_tasks(self):
        # Initially user A has no tasks
        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(len(tasks), 0)

        # Create tasks for user A
        self.test_db.create_task("task_1", self.user_a["id"], "Finish project report", "Work")
        self.test_db.create_task("task_2", self.user_a["id"], "Buy groceries", "Personal")

        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["title"], "Buy groceries")
        self.assertEqual(tasks[0]["tag"], "Personal")
        self.assertEqual(tasks[0]["completed"], 0)

    def test_toggle_task_completion(self):
        self.test_db.create_task("task_1", self.user_a["id"], "Check emails", "Work")
        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(tasks[0]["completed"], 0)

        # Mark as completed
        self.test_db.toggle_task("task_1", self.user_a["id"], True)
        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(tasks[0]["completed"], 1)

        # Toggle back to incomplete
        self.test_db.toggle_task("task_1", self.user_a["id"], False)
        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(tasks[0]["completed"], 0)

    def test_update_task(self):
        self.test_db.create_task("task_1", self.user_a["id"], "Initial Title", "General")
        
        # Update title only
        self.test_db.update_task("task_1", self.user_a["id"], "Updated Title")
        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(tasks[0]["title"], "Updated Title")
        self.assertEqual(tasks[0]["tag"], "General")

        # Update title and tag
        self.test_db.update_task("task_1", self.user_a["id"], "Final Title", "Urgent")
        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(tasks[0]["title"], "Final Title")
        self.assertEqual(tasks[0]["tag"], "Urgent")

    def test_delete_task(self):
        self.test_db.create_task("task_1", self.user_a["id"], "Task 1", "General")
        self.test_db.create_task("task_2", self.user_a["id"], "Task 2", "General")
        self.assertEqual(len(self.test_db.get_user_tasks(self.user_a["id"])), 2)

        self.test_db.delete_task("task_1", self.user_a["id"])
        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["id"], "task_2")

    def test_clear_completed_tasks(self):
        self.test_db.create_task("task_1", self.user_a["id"], "Task 1", "General")
        self.test_db.create_task("task_2", self.user_a["id"], "Task 2", "General")
        self.test_db.create_task("task_3", self.user_a["id"], "Task 3", "General")

        self.test_db.toggle_task("task_1", self.user_a["id"], True)
        self.test_db.toggle_task("task_3", self.user_a["id"], True)

        self.test_db.clear_completed_tasks(self.user_a["id"])
        tasks = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["id"], "task_2")
        self.assertEqual(tasks[0]["completed"], 0)

    def test_user_isolation(self):
        # User A creates a task
        self.test_db.create_task("task_a", self.user_a["id"], "User A Secret Task", "Personal")
        # User B creates a task
        self.test_db.create_task("task_b", self.user_b["id"], "User B Work Task", "Work")

        # Verify User A only sees their task
        tasks_a = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(len(tasks_a), 1)
        self.assertEqual(tasks_a[0]["title"], "User A Secret Task")

        # Verify User B only sees their task
        tasks_b = self.test_db.get_user_tasks(self.user_b["id"])
        self.assertEqual(len(tasks_b), 1)
        self.assertEqual(tasks_b[0]["title"], "User B Work Task")

        # User B cannot toggle User A's task
        self.test_db.toggle_task("task_a", self.user_b["id"], True)
        tasks_a = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(tasks_a[0]["completed"], 0)

        # User B cannot delete User A's task
        self.test_db.delete_task("task_a", self.user_b["id"])
        tasks_a = self.test_db.get_user_tasks(self.user_a["id"])
        self.assertEqual(len(tasks_a), 1)


if __name__ == "__main__":
    unittest.main()
