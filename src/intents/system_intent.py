import re
from src.system_control import system_controller


class SystemAutomationIntent:

    def __init__(self, brain=None):
        self.brain = brain
        self.controller = system_controller

    def process(self, user_message: str, user_id: str = "default_user") -> str | None:
        message = user_message.strip()
        lower = message.lower()

        # 0. Check Alarm Audio Test Commands
        # e.g. "test alarm", "test alarm sound", "ring alarm", "play alarm sound", "test chime"
        if lower in [
            "test alarm", "test alarm sound", "test the alarm", "ring alarm",
            "sound alarm", "play alarm sound", "test chime", "test alarm audio"
        ]:
            res = self.controller.test_alarm()
            return res["message"]

        # 1. Check Alarm Cancellation Commands
        # e.g. "cancel alarm", "delete alarm", "clear alarms", "turn off alarm", "stop alarm"
        if lower in [
            "cancel alarm", "cancel alarms", "delete alarm", "delete alarms",
            "clear alarm", "clear alarms", "stop alarm", "stop alarms",
            "turn off alarm", "turn off alarms", "remove alarm", "remove alarms",
            "cancel my alarm", "delete my alarm", "stop the alarm"
        ]:
            res = self.controller.cancel_alarm(user_id=user_id)
            return res["message"]

        # 2. Check Alarm Status, Location, and Query Commands
        # e.g. "where is the alarm", "where you have set alarm?", "no alarm is set",
        # "i have set an alarm but no alarm is set to alarm", "show active alarms", "my alarms"
        non_alarm_domains = ["weather", "project", "memory", "email", "briefing"]
        if not any(d in lower for d in non_alarm_domains):
            alarm_query_patterns = [
                r'where.*alarm',
                r'where.*to.*check',
                r'where.*check',
                r'how.*check.*alarm',
                r'no\s+alarm',
                r'no\s+alarm\s+is\s+set',
                r'alarm\s+is\s+not\s+set',
                r'not\s+set\s+to\s+alarm',
                r'did\s+you\s+set.*alarm',
                r'alarm\s+status',
                r'show.*alarm',
                r'list.*alarm',
                r'my\s+alarms',
                r'active\s+alarms',
                r'check.*alarm',
                r'alarm.*set\?'
            ]
            if any(re.search(pat, lower) for pat in alarm_query_patterns):
                active = self.controller.get_active_alarms(user_id)
                if active:
                    items = "\n".join([f"- **Target Time**: **{a['target_time']}** ({a['countdown']}) | Label: *{a['label']}*" for a in active])
                    return (
                        f"**Active Scheduled Alarms in NOVAX-AI**\n\n"
                        f"{items}\n\n"
                        f"**Where Your Alarm is Configured & How It Rings**:\n"
                        f"1. **Audible Speaker Chime**: NOVAX-AI background audio daemon is running on your Mac and will sound a native chime (`Glass.aiff`) at the scheduled time.\n"
                        f"2. **macOS Desktop Banner**: A system alert banner with sound will trigger.\n"
                        f"3. **Apple Reminders**: Scheduled reminder created in macOS Reminders.\n"
                        f"4. **macOS Clock App**: Opened directly to the Alarms tab.\n\n"
                        f"Commands: Type **`test alarm`** to hear the chime now, **`cancel alarm`** to cancel, or **`set an alarm at [time]`** to schedule a new one."
                    )
                else:
                    return (
                        f"**Alarm Status: No Active Alarms Currently Scheduled**\n\n"
                        f"There are currently no active alarms scheduled in NOVAX-AI.\n\n"
                        f"**How to Set an Alarm**:\n"
                        f"- Type: **`set an alarm at 12:04 PM`** or **`set an alarm in 5 minutes`**\n"
                        f"- Or enter a time: **`12:04 PM`** or **`7:30 AM`**\n\n"
                        f"**How NOVAX-AI Alarms Work on Your Mac**:\n"
                        f"- When you set an alarm, NOVAX-AI arms an audible background daemon on your Mac that sounds a native chime (`Glass.aiff`), posts a macOS desktop alert banner, adds a scheduled reminder in Apple Reminders, and opens the macOS Clock app.\n\n"
                        f"💡 Type **`test alarm`** to verify your Mac's speaker chime right now."
                    )

        # 3. Check Alarm Scheduling Commands
        # e.g. "set an alarm at 12 04", "set alarm for 7:30 AM", "alarm at 6:00 pm", "wake me up at 7 am", "set alarm 12", "alarm in 10 minutes"
        alarm_match = re.search(
            r'^(?:please\s+)?(?:set\s+(?:an?\s+)?)?alarm\s+(?:at|for|to)?\s*([0-9\:\.\sapm\.\'\"]+)(?:\s+(?:for|called|named|label)\s+(.+))?$',
            lower
        )
        if not alarm_match:
            wake_match = re.search(
                r'^(?:please\s+)?wake\s+(?:me\s+)?(?:up\s+)?at\s*([0-9\:\.\sapm\.\'\"]+)(?:\s+(?:for|called|named|label)\s+(.+))?$',
                lower
            )
            if wake_match:
                alarm_match = wake_match

        if not alarm_match:
            rel_alarm_match = re.search(
                r'^(?:please\s+)?(?:set\s+(?:an?\s+)?)?alarm\s+(in\s+[0-9\.\s\w]+)(?:\s+(?:for|called|named|label)\s+(.+))?$',
                lower
            )
            if rel_alarm_match:
                alarm_match = rel_alarm_match

        if not alarm_match:
            # Check bare time input: e.g. "12:04 pm", "12 04", "12.04", "at 12:04 pm", "7:30 am", "6 pm"
            time_only_match = re.match(
                r'^(?:at\s+)?(\d{1,2}(?:[\:\.\s]+\d{2})?\s*(?:am|pm)?|\d{1,2}[\:\.\s]+\d{2})$',
                lower
            )
            if time_only_match:
                alarm_match = time_only_match

        if alarm_match:
            time_raw = alarm_match.group(1).strip(' "\'')
            label = "Alarm"
            if alarm_match.lastindex and alarm_match.lastindex >= 2 and alarm_match.group(2):
                label = alarm_match.group(2).strip(' "\'').capitalize()

            if time_raw:
                res = self.controller.schedule_alarm(time_raw, label=label, user_id=user_id)
                if res.get("success"):
                    return res["message"]
                return res.get("message", "Unable to schedule alarm.")

        # 4. Check Timer Commands
        # e.g. "set a timer for 10 minutes", "timer 5 min", "start a timer for 30 seconds"
        timer_match = re.search(
            r'^(?:please\s+)?(?:set|start|begin)?\s*(?:an?\s+)?timer\s+(?:for|in|of)?\s*([0-9\.\s\w]+?)(?:\s+(?:for|called|named|label)\s+(.+))?$',
            lower
        )
        if timer_match:
            dur_raw = timer_match.group(1).strip(' "\'')
            label = "Timer"
            if timer_match.lastindex and timer_match.lastindex >= 2 and timer_match.group(2):
                label = timer_match.group(2).strip(' "\'').capitalize()

            if dur_raw:
                res = self.controller.schedule_timer(dur_raw, label=label, user_id=user_id)
                if res.get("success"):
                    return res["message"]

        # 5. Check App Launch Commands
        # e.g. "open Clock", "open Calculator", "launch Notes", "start Terminal", "open Safari"
        app_match = re.search(
            r'^(?:please\s+)?(?:open|launch|start)\s+(?:the\s+)?([a-zA-Z0-9\s]+?)(?:\s+app)?$',
            lower
        )
        if app_match:
            app_raw = app_match.group(1).strip()
            is_known_app = app_raw in self.controller.APP_MAP or lower.endswith(" app") or lower.endswith("app")
            non_apps = [
                "conversation", "conversations", "chat", "project", "projects",
                "task", "tasks", "memory", "file", "document", "settings",
                "profile", "backup", "me", "code", "quicksort", "python"
            ]
            if is_known_app and app_raw not in non_apps and not any(app_raw.startswith(na) for na in non_apps):
                res = self.controller.open_app(app_raw)
                return res["message"]

        # 6. Check Volume / Audio Control Commands
        # e.g. "set volume to 50%", "volume 70", "mute volume", "unmute"
        if lower in ["mute", "mute volume", "mute sound", "mute audio", "silence"]:
            res = self.controller.mute_volume(True)
            return res["message"]
        elif lower in ["unmute", "unmute volume", "unmute sound", "unmute audio"]:
            res = self.controller.mute_volume(False)
            return res["message"]

        vol_match = re.search(r'^(?:set\s+)?volume\s+(?:to\s+)?(\d{1,3})\s*%?$', lower)
        if vol_match:
            pct = int(vol_match.group(1))
            res = self.controller.set_volume(pct)
            return res["message"]

        return None
