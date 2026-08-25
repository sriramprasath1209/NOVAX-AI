import importlib.util
from datetime import datetime
try:
    import zoneinfo
except ImportError:
    zoneinfo = None

from src.system_prompt import SYSTEM_PROMPT


class AIModel:

    def _get_current_time_ist(self):
        try:
            if zoneinfo:
                tz = zoneinfo.ZoneInfo("Asia/Kolkata")
                now = datetime.now(tz)
            else:
                now = datetime.now()
            return now.strftime("%A, %B %d, %Y at %I:%M:%S %p IST")
        except Exception:
            return datetime.now().strftime("%A, %B %d, %Y at %I:%M %p IST")

    def ask(self, messages):
        ollama_available = importlib.util.find_spec("ollama") is not None
        time_context = f"\n\n[Current Live Context]\nExact Current Date & Time: {self._get_current_time_ist()}"
        full_system_prompt = SYSTEM_PROMPT + time_context

        if ollama_available:
            try:
                import ollama

                response = ollama.chat(
                    model="gemma3",
                    messages=[
                        {
                            "role": "system",
                            "content": full_system_prompt
                        }
                    ] + messages
                )

                return response["message"]["content"]

            except Exception as error:
                return self._fallback_response(messages, error)

        return self._fallback_response(messages)

    def _fallback_response(self, messages, error=None):
        latest_message = messages[-1]["content"] if messages else ""
        latest_message = latest_message.strip() or "your message"

        return (
            f"NOVAX-AI model Ollama is not active right now. Please make sure the Ollama model is running in the background. "
            f"I heard: {latest_message}. I can still help with chat, memory, and quick assistance."
        )