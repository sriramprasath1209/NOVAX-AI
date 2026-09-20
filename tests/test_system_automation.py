import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.db import Database
from src import auth
from src.system_control import SystemController
from src.intents.system_intent import SystemAutomationIntent
from src.intent import IntentManager


class SystemAutomationTests(unittest.TestCase):

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()

        self.test_db = Database(self.db_path)
        auth.db = self.test_db

        self.db_patcher = patch("src.system_control.db", self.test_db)
        self.db_patcher.start()

        self.user, _ = auth.register_user("tony@stark.com", "ironman123", "Tony Stark")
        self.controller = SystemController()
        self.intent = SystemAutomationIntent()
        self.intent_manager = IntentManager()

    def tearDown(self):
        self.db_patcher.stop()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_parse_target_time(self):
        # Test exact hours
        dt12, str12 = self.controller.parse_target_time("12")
        self.assertIsNotNone(dt12)
        self.assertEqual(dt12.minute, 0)
        self.assertIn("12:00", str12)

        # Test AM/PM
        dt_am, str_am = self.controller.parse_target_time("7:30 AM")
        self.assertIsNotNone(dt_am)
        self.assertEqual(dt_am.hour, 7)
        self.assertEqual(dt_am.minute, 30)
        self.assertEqual(str_am, "7:30 AM")

        # AM/PM and 24h tests
        dt_pm, str_pm = self.controller.parse_target_time("6 PM")
        self.assertIsNotNone(dt_pm)
        self.assertEqual(dt_pm.hour, 18)
        self.assertEqual(str_pm, "6:00 PM")

        # Flexible formats: space separated "12 04", dot separated "12.04"
        dt_space, str_space = self.controller.parse_target_time("12 04")
        self.assertIsNotNone(dt_space)
        self.assertEqual(dt_space.minute, 4)

        dt_dot, str_dot = self.controller.parse_target_time("12.04 pm")
        self.assertIsNotNone(dt_dot)
        self.assertEqual(dt_dot.hour, 12)
        self.assertEqual(dt_dot.minute, 4)

        # Relative time
        dt_rel, str_rel = self.controller.parse_target_time("in 15 minutes")
        self.assertIsNotNone(dt_rel)

    def test_parse_duration_seconds(self):
        secs, disp = self.controller.parse_duration_seconds("10 minutes")
        self.assertEqual(secs, 600)
        self.assertIn("10 minute(s)", disp)

        secs_s, disp_s = self.controller.parse_duration_seconds("45 seconds")
        self.assertEqual(secs_s, 45)
        self.assertIn("45 second(s)", disp_s)

        secs_h, disp_h = self.controller.parse_duration_seconds("1.5 hours")
        self.assertEqual(secs_h, 5400)
        self.assertIn("1.5 hour(s)", disp_h)

    @patch("subprocess.run")
    def test_schedule_alarm_and_task_sync(self, mock_subproc):
        mock_subproc.return_value = MagicMock(returncode=0)

        res = self.controller.schedule_alarm("12", label="Team Standup", user_id=self.user["id"])
        self.assertTrue(res["success"])
        self.assertIn("Alarm Set Successfully", res["message"])
        self.assertIn("Team Standup", res["message"])

        # Verify task was created in DB
        tasks = self.test_db.get_user_tasks(self.user["id"])
        self.assertEqual(len(tasks), 1)
        self.assertIn("[Alarm]", tasks[0]["title"])
        self.assertIn("Team Standup", tasks[0]["title"])
        self.assertEqual(tasks[0]["tag"], "Alarm")

        # Verify get_active_alarms
        active = self.controller.get_active_alarms(user_id=self.user["id"])
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["label"], "Team Standup")

        # Verify cancel_alarm
        cancel_res = self.controller.cancel_alarm(user_id=self.user["id"])
        self.assertTrue(cancel_res["success"])
        self.assertEqual(len(self.controller.get_active_alarms(user_id=self.user["id"])), 0)

    @patch("subprocess.run")
    def test_alarm_audio_test(self, mock_subproc):
        mock_subproc.return_value = MagicMock(returncode=0)
        res = self.controller.test_alarm()
        self.assertTrue(res["success"])
        self.assertIn("Alarm Sound & Notification Test Triggered", res["message"])

    @patch("subprocess.run")
    def test_schedule_timer(self, mock_subproc):
        mock_subproc.return_value = MagicMock(returncode=0)

        res = self.controller.schedule_timer("5 minutes", label="Pomodoro", user_id=self.user["id"])
        self.assertTrue(res["success"])
        self.assertIn("Timer Set Successfully", res["message"])
        self.assertIn("5 minute(s)", res["message"])

        tasks = self.test_db.get_user_tasks(self.user["id"])
        self.assertEqual(len(tasks), 1)
        self.assertIn("[Timer]", tasks[0]["title"])

    @patch("subprocess.run")
    def test_open_app(self, mock_subproc):
        mock_subproc.return_value = MagicMock(returncode=0)

        res = self.controller.open_app("Clock")
        self.assertTrue(res["success"])
        self.assertIn("Clock", res["message"])

        res_calc = self.controller.open_app("calculator")
        self.assertTrue(res_calc["success"])
        self.assertIn("Calculator", res_calc["message"])

    @patch("subprocess.run")
    def test_volume_controls(self, mock_subproc):
        mock_subproc.return_value = MagicMock(returncode=0)

        res_vol = self.controller.set_volume(75)
        self.assertTrue(res_vol["success"])
        self.assertEqual(res_vol["volume"], 75)

        res_mute = self.controller.mute_volume(True)
        self.assertTrue(res_mute["success"])
        self.assertTrue(res_mute["muted"])

    @patch("subprocess.run")
    def test_system_intent_parsing(self, mock_subproc):
        mock_subproc.return_value = MagicMock(returncode=0)

        # 1. "set an alarm at 12"
        reply = self.intent.process("set an alarm at 12", user_id=self.user["id"])
        self.assertIsNotNone(reply)
        self.assertIn("Alarm Set Successfully", reply)
        self.assertIn("Clock App", reply)

        # 2. "wake me up at 7:30 am"
        reply_wake = self.intent.process("wake me up at 7:30 am", user_id=self.user["id"])
        self.assertIsNotNone(reply_wake)
        self.assertIn("7:30 AM", reply_wake)

        # 3. Flexible format "set an alarm at 12 04"
        reply_space = self.intent.process("set an alarm at 12 04", user_id=self.user["id"])
        self.assertIsNotNone(reply_space)
        self.assertIn("Alarm Set Successfully", reply_space)

        # 4. Bare time input "12:04 pm"
        reply_time = self.intent.process("12:04 pm", user_id=self.user["id"])
        self.assertIsNotNone(reply_time)
        self.assertIn("Alarm Set Successfully", reply_time)

        # 5. Query active alarms / where is alarm
        reply_query = self.intent.process("where is the alarm", user_id=self.user["id"])
        self.assertIsNotNone(reply_query)
        self.assertIn("Active Scheduled Alarms", reply_query)

        # 6. User asking "i have set an alarm but no alarm is set to alarm"
        reply_user_query = self.intent.process("i have set an alarm but no alarm is set to alarm", user_id=self.user["id"])
        self.assertIsNotNone(reply_user_query)
        self.assertIn("Active Scheduled Alarms", reply_user_query)

        # 7. Test alarm sound
        reply_test = self.intent.process("test alarm", user_id=self.user["id"])
        self.assertIsNotNone(reply_test)
        self.assertIn("Alarm Sound & Notification Test Triggered", reply_test)

        # 8. Cancel alarms
        reply_cancel = self.intent.process("cancel alarm", user_id=self.user["id"])
        self.assertIsNotNone(reply_cancel)
        self.assertIn("cancelled", reply_cancel.lower())

        # 9. "open Calculator"
        reply_app = self.intent.process("open Calculator", user_id=self.user["id"])
        self.assertIsNotNone(reply_app)
        self.assertIn("Calculator", reply_app)

        # 10. "set volume to 60%"
        reply_vol = self.intent.process("set volume to 60%", user_id=self.user["id"])
        self.assertIsNotNone(reply_vol)
        self.assertIn("60%", reply_vol)

    @patch("subprocess.run")
    def test_intent_manager_integration(self, mock_subproc):
        mock_subproc.return_value = MagicMock(returncode=0)

        reply = self.intent_manager.process("set an alarm at 12", user_id=self.user["id"])
        self.assertIsNotNone(reply)
        self.assertIn("Alarm Set Successfully", reply)


if __name__ == "__main__":
    unittest.main()
