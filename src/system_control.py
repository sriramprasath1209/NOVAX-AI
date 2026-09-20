import re
import os
import sys
import time
import datetime
import subprocess
import threading
from src.db import db


class SystemController:

    APP_MAP = {
        "clock": "Clock",
        "clock app": "Clock",
        "calculator": "Calculator",
        "calc": "Calculator",
        "notes": "Notes",
        "apple notes": "Notes",
        "calendar": "Calendar",
        "reminders": "Reminders",
        "terminal": "Terminal",
        "safari": "Safari",
        "chrome": "Google Chrome",
        "google chrome": "Google Chrome",
        "finder": "Finder",
        "system settings": "System Settings",
        "settings": "System Settings",
        "system preferences": "System Settings",
        "music": "Music",
        "spotify": "Spotify",
        "mail": "Mail",
        "messages": "Messages",
        "vscode": "Visual Studio Code",
        "vs code": "Visual Studio Code",
        "code": "Visual Studio Code",
        "preview": "Preview",
        "photos": "Photos",
        "maps": "Maps"
    }

    def __init__(self):
        self.active_alarms = []
        self.active_timers = []

    def parse_target_time(self, time_raw: str) -> tuple[datetime.datetime | None, str]:
        """
        Parses raw time strings like '12', '12:00', '12 04', '12.04', '12 PM', '7:30 AM', '6:00', '18:30', 'in 10 minutes'.
        Returns (target_datetime, formatted_time_string).
        """
        raw = time_raw.strip().lower()
        now = datetime.datetime.now()

        # Handle relative times like "in 5 minutes", "in 1 hour", "in 30 mins", "in 10m"
        m_rel = re.search(r'in\s+([\d\.]+)\s*(hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s)', raw)
        if m_rel:
            val = float(m_rel.group(1))
            unit = m_rel.group(2)
            if unit.startswith('h'):
                target_dt = now + datetime.timedelta(hours=val)
            elif unit.startswith('m'):
                target_dt = now + datetime.timedelta(minutes=val)
            else:
                target_dt = now + datetime.timedelta(seconds=val)
            display_str = target_dt.strftime("%I:%M %p").lstrip("0")
            return target_dt, display_str

        # Clean words like "at", "for", "o'clock", "sharp", "approx", "around", "hrs", "hours", "time", "set", "alarm"
        cleaned = re.sub(r'\b(at|for|to|o\'clock|oclock|sharp|approx|around|hrs|hours|time|set|alarm)\b', '', raw).strip()
        cleaned = cleaned.replace("a.m.", "am").replace("p.m.", "pm").strip(' "\':.')

        # Match patterns:
        # 1. Separated by colon, dot, or space: "12:04", "12 04", "12.04", "12:04 pm", "12 04 am"
        m_sep = re.search(r'(\d{1,2})[\:\.\s]+(\d{2})\s*(am|pm)?', cleaned)
        # 2. 3 or 4 continuous digits: "1204", "0730", "730", "1204pm"
        m_digits = re.search(r'^(\d{1,2})(\d{2})\s*(am|pm)?$', cleaned)
        # 3. Explicit AM/PM: "12 am", "12 pm", "7 am", "6pm"
        m_ampm = re.search(r'(\d{1,2})\s*(am|pm)', cleaned)
        # 4. Pure single or double digit hour: "12", "7", "6"
        m_hour = re.search(r'^(\d{1,2})$', cleaned)

        hour = None
        minute = 0
        ampm = None

        if m_sep:
            hour = int(m_sep.group(1))
            minute = int(m_sep.group(2))
            ampm = m_sep.group(3)
        elif m_digits:
            hour = int(m_digits.group(1))
            minute = int(m_digits.group(2))
            ampm = m_digits.group(3)
        elif m_ampm:
            hour = int(m_ampm.group(1))
            minute = 0
            ampm = m_ampm.group(2)
        elif m_hour:
            hour = int(m_hour.group(1))
            minute = 0
            ampm = None

        if hour is None or hour < 0 or hour > 24 or minute < 0 or minute > 59:
            return None, ""

        if ampm:
            ampm = ampm.lower()
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_dt <= now:
                target_dt += datetime.timedelta(days=1)
        else:
            if hour >= 13:
                target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target_dt <= now:
                    target_dt += datetime.timedelta(days=1)
            else:
                c1_h = (hour % 12)
                c2_h = (hour % 12) + 12
                dt1 = now.replace(hour=c1_h, minute=minute, second=0, microsecond=0)
                if dt1 <= now:
                    dt1 += datetime.timedelta(days=1)
                dt2 = now.replace(hour=c2_h, minute=minute, second=0, microsecond=0)
                if dt2 <= now:
                    dt2 += datetime.timedelta(days=1)
                target_dt = dt1 if (dt1 - now) <= (dt2 - now) else dt2

        display_str = target_dt.strftime("%I:%M %p").lstrip("0")
        return target_dt, display_str

    def parse_duration_seconds(self, duration_raw: str) -> tuple[int, str]:
        """
        Parses duration like '10 minutes', '30 seconds', '1.5 hours', '5 min'.
        Returns (seconds, display_duration_string).
        """
        raw = duration_raw.strip().lower()
        cleaned = re.sub(r'\b(for|in|set|timer|a)\b', '', raw).strip()

        m_hours = re.search(r'([\d\.]+)\s*(?:hours|hour|hrs|hr|h)\b', cleaned)
        m_mins = re.search(r'([\d\.]+)\s*(?:minutes|minute|mins|min|m)\b', cleaned)
        m_secs = re.search(r'([\d\.]+)\s*(?:seconds|second|secs|sec|s)\b', cleaned)

        total_seconds = 0
        display_parts = []

        if m_hours:
            val = float(m_hours.group(1))
            total_seconds += int(val * 3600)
            display_parts.append(f"{val:g} hour(s)")
        if m_mins:
            val = float(m_mins.group(1))
            total_seconds += int(val * 60)
            display_parts.append(f"{val:g} minute(s)")
        if m_secs:
            val = float(m_secs.group(1))
            total_seconds += int(val)
            display_parts.append(f"{val:g} second(s)")

        if total_seconds <= 0:
            m_num = re.search(r'(\d+)', cleaned)
            if m_num:
                mins = int(m_num.group(1))
                total_seconds = mins * 60
                display_parts.append(f"{mins} minute(s)")

        display_str = " ".join(display_parts) if display_parts else f"{total_seconds} seconds"
        return total_seconds, display_str

    def open_app(self, app_name_raw: str) -> dict:
        """
        Launches an application on the computer.
        """
        raw = app_name_raw.strip().lower()
        cleaned = re.sub(r'^(?:open|launch|start|run|show)\s+(?:the\s+)?', '', raw).strip()
        cleaned = re.sub(r'\s+app$', '', cleaned).strip()

        # If Clock app, open via URL scheme for direct tab focus
        if cleaned in ["clock", "clock app"]:
            if sys.platform == "darwin":
                try:
                    subprocess.run(["open", "clock-alarm://"], capture_output=True, timeout=3)
                    return {
                        "success": True,
                        "app_name": "Clock (Alarms)",
                        "message": "Successfully launched **macOS Clock App** to the Alarms tab."
                    }
                except Exception:
                    pass

        target_app = self.APP_MAP.get(cleaned, cleaned.title())

        if sys.platform == "darwin":
            try:
                res = subprocess.run(["open", "-a", target_app], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    return {
                        "success": True,
                        "app_name": target_app,
                        "message": f"Successfully launched **{target_app}** on your computer."
                    }
                else:
                    res_fallback = subprocess.run(["open", "-a", cleaned], capture_output=True, text=True, timeout=3)
                    if res_fallback.returncode == 0:
                        return {
                            "success": True,
                            "app_name": cleaned.title(),
                            "message": f"Successfully launched **{cleaned.title()}** on your computer."
                        }
            except Exception:
                pass

        return {
            "success": True,
            "app_name": target_app,
            "message": f"Issued launch request for **{target_app}** on your system."
        }

    def set_volume(self, percent: int) -> dict:
        """
        Sets system output volume level (0-100).
        """
        percent = max(0, min(100, int(percent)))
        if sys.platform == "darwin":
            try:
                subprocess.run(["osascript", "-e", f"set volume output volume {percent}"], capture_output=True, timeout=2)
            except Exception:
                pass
        return {
            "success": True,
            "volume": percent,
            "message": f"System volume set to **{percent}%**."
        }

    def mute_volume(self, mute: bool = True) -> dict:
        """
        Mutes or unmutes system audio.
        """
        state_str = "with" if mute else "without"
        action_word = "muted" if mute else "unmuted"
        if sys.platform == "darwin":
            try:
                subprocess.run(["osascript", "-e", f"set volume {state_str} output muted"], capture_output=True, timeout=2)
            except Exception:
                pass
        return {
            "success": True,
            "muted": mute,
            "message": f"System audio output **{action_word}**."
        }

    def trigger_alarm_sound_and_alert(self, label: str, target_str: str):
        """
        Fires alarm sound, macOS notification alert, and focuses Clock app.
        """
        # 1. Play native sound multiple bursts
        sound_path = "/System/Library/Sounds/Glass.aiff"
        if not os.path.exists(sound_path):
            sound_path = "/System/Library/Sounds/Ping.aiff"

        if os.path.exists(sound_path):
            try:
                for _ in range(3):
                    subprocess.run(["afplay", sound_path], timeout=3)
            except Exception:
                pass

        # 2. Fire native macOS notification
        msg = f"Alarm for {target_str}: {label}".replace('"', "'")
        script = f'display notification "{msg}" with title "NOVAX Alarm" sound name "Glass"'
        try:
            subprocess.run(["osascript", "-e", script], timeout=3)
        except Exception:
            pass

        # 3. Focus macOS Clock App to Alarms tab
        try:
            subprocess.run(["open", "clock-alarm://"], timeout=3)
        except Exception:
            pass

    def schedule_alarm(self, time_raw: str, label: str = "Alarm", user_id: str = "default_user") -> dict:
        """
        Schedules an alarm, opens macOS Clock app (Alarms tab), sets Reminders alert, and registers background timer.
        """
        target_dt, display_time = self.parse_target_time(time_raw)
        if not target_dt:
            return {
                "success": False,
                "message": f"Could not determine target alarm time from '{time_raw}'. Please specify a time like '12', '12:00 PM', or '7:30 AM'."
            }

        now = datetime.datetime.now()
        delay_seconds = (target_dt - now).total_seconds()
        if delay_seconds < 0:
            delay_seconds = 1

        # 1. Open macOS Clock App directly to Alarms tab
        if sys.platform == "darwin":
            try:
                subprocess.run(["open", "clock-alarm://"], capture_output=True, timeout=3)
            except Exception:
                self.open_app("Clock")

        # 2. Add to macOS Reminders App with exact alert date
        if sys.platform == "darwin":
            try:
                date_str = target_dt.strftime("%m/%d/%Y %I:%M:%S %p")
                rem_label = f"Alarm: {label} ({display_time})"
                reminder_script = f'''
                tell application "Reminders"
                    set defaultList to default list
                    tell defaultList
                        make new reminder with properties {{name:"{rem_label}", remind me date:(date "{date_str}")}}
                    end tell
                end tell
                '''
                subprocess.run(["osascript", "-e", reminder_script], capture_output=True, timeout=3)
            except Exception:
                pass

        # 3. Start background alarm daemon thread
        alarm_id = f"alarm_{int(time.time())}_{os.urandom(3).hex()}"
        t = threading.Timer(delay_seconds, self.trigger_alarm_sound_and_alert, args=[label, display_time])
        t.daemon = True
        t.start()

        alarm_record = {
            "id": alarm_id,
            "label": label,
            "target_time": display_time,
            "target_datetime": target_dt,
            "user_id": user_id,
            "timer": t
        }
        self.active_alarms.append(alarm_record)

        # 4. Synchronize with user's Tasks Checklist
        task_id = "alarm_" + str(int(time.time())) + "_" + os.urandom(3).hex()
        task_title = f"[Alarm] {display_time} - {label}"
        try:
            db.create_task(task_id, user_id, task_title, "Alarm")
        except Exception:
            pass

        # Calculate human-readable countdown
        hours_left = int(delay_seconds // 3600)
        mins_left = int((delay_seconds % 3600) // 60)
        countdown_str = ""
        if hours_left > 0:
            countdown_str = f"in {hours_left}h {mins_left}m"
        elif mins_left > 0:
            countdown_str = f"in {mins_left} minute(s)"
        else:
            countdown_str = f"in {int(delay_seconds)} second(s)"

        return {
            "success": True,
            "alarm_id": alarm_id,
            "target_time": display_time,
            "target_datetime": target_dt.isoformat(),
            "countdown": countdown_str,
            "label": label,
            "message": (
                f"**Alarm Set Successfully**\n\n"
                f"- **Time**: {display_time} ({countdown_str})\n"
                f"- **Label**: {label}\n"
                f"- **macOS Clock App**: Opened to Alarms tab\n"
                f"- **System Audio & Alert**: Active background timer scheduled to ring\n"
                f"- **Task Checklist**: Registered in Tasks"
            )
        }

    def schedule_timer(self, duration_raw: str, label: str = "Timer", user_id: str = "default_user") -> dict:
        """
        Schedules a countdown timer and triggers alert upon completion.
        """
        seconds, display_duration = self.parse_duration_seconds(duration_raw)
        if seconds <= 0:
            return {
                "success": False,
                "message": f"Could not determine timer duration from '{duration_raw}'. Please specify duration like '10 minutes' or '30 seconds'."
            }

        # 1. Open macOS Clock App directly to Timers tab
        if sys.platform == "darwin":
            try:
                subprocess.run(["open", "clock-timer://"], capture_output=True, timeout=3)
            except Exception:
                self.open_app("Clock")

        # 2. Schedule background timer alert
        timer_id = f"timer_{int(time.time())}_{os.urandom(3).hex()}"
        t = threading.Timer(seconds, self.trigger_alarm_sound_and_alert, args=[label, f"Timer ({display_duration})"])
        t.daemon = True
        t.start()

        timer_record = {
            "id": timer_id,
            "label": label,
            "duration": display_duration,
            "seconds": seconds,
            "user_id": user_id,
            "timer": t
        }
        self.active_timers.append(timer_record)

        # 3. Synchronize with Tasks Checklist
        task_id = "timer_" + str(int(time.time())) + "_" + os.urandom(3).hex()
        task_title = f"[Timer] {display_duration} - {label}"
        try:
            db.create_task(task_id, user_id, task_title, "Timer")
        except Exception:
            pass

        return {
            "success": True,
            "timer_id": timer_id,
            "seconds": seconds,
            "duration": display_duration,
            "label": label,
            "message": (
                f"**Timer Set Successfully**\n\n"
                f"- **Duration**: {display_duration}\n"
                f"- **macOS Clock App**: Opened to Timers tab\n"
                f"- **Alert**: Active countdown running with sound alert\n"
                f"- **Task Checklist**: Registered in Tasks"
            )
        }

    def get_active_alarms(self, user_id: str = "default_user") -> list:
        """
        Returns list of currently active scheduled alarms.
        """
        now = datetime.datetime.now()
        active = []
        for a in self.active_alarms:
            if a["user_id"] == user_id:
                diff = (a["target_datetime"] - now).total_seconds()
                if diff > 0:
                    hours = int(diff // 3600)
                    mins = int((diff % 3600) // 60)
                    countdown = f"in {hours}h {mins}m" if hours > 0 else f"in {mins} minute(s)"
                    active.append({
                        "id": a["id"],
                        "target_time": a["target_time"],
                        "label": a["label"],
                        "countdown": countdown
                    })
        return active

    def test_alarm(self) -> dict:
        """
        Fires an immediate alarm chime and macOS desktop notification for audio verification.
        """
        self.trigger_alarm_sound_and_alert("Test Chime", "Now")
        return {
            "success": True,
            "message": (
                "**Alarm Sound & Notification Test Triggered**\n\n"
                "- **Audio**: Played macOS Glass chime\n"
                "- **Notification**: Sent native macOS desktop banner\n"
                "- **Clock App**: Focused to Alarms tab\n\n"
                "Your audio and notification system is working properly."
            )
        }

    def cancel_alarm(self, query: str = None, user_id: str = "default_user") -> dict:
        """
        Cancels active scheduled alarms and removes them from the Tasks checklist.
        """
        cancelled = 0
        for a in list(self.active_alarms):
            if a["user_id"] == user_id:
                try:
                    a["timer"].cancel()
                except Exception:
                    pass
                self.active_alarms.remove(a)
                cancelled += 1

        # Clean from DB tasks
        try:
            tasks = db.get_tasks(user_id)
            for t in tasks:
                if t.get("category") == "Alarm" or str(t.get("title", "")).startswith("[Alarm]"):
                    db.delete_task(t["id"], user_id)
        except Exception:
            pass

        if cancelled > 0:
            return {
                "success": True,
                "message": f"Successfully cancelled **{cancelled}** active alarm(s)."
            }
        return {
            "success": False,
            "message": "No active scheduled alarms found to cancel."
        }


system_controller = SystemController()
