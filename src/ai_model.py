import importlib.util

from src.system_prompt import SYSTEM_PROMPT


class AIModel:

    def ask(self, messages):
        ollama_available = importlib.util.find_spec("ollama") is not None

        if ollama_available:
            try:
                import ollama

                response = ollama.chat(
                    model="gemma3",
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
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

        if error:
            return (
                f"NOVAX-AI is running in offline mode right now because the model service is unavailable. "
                f"I heard: {latest_message}. I can still help with chat, memory, and quick assistance."
            )

        return (
            f"NOVAX-AI is running in offline mode right now. I heard: {latest_message}. "
            "I can still help with chat, memory, and quick assistance."
        )