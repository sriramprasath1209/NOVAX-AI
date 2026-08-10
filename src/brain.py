from src.ai_model import AIModel
from src.conversation import Conversation
from src.memory import MemoryManager
from src.intent import IntentManager


class Brain:

    def __init__(self):
        self.ai = AIModel()
        self.conversation = Conversation()
        self.memory = MemoryManager()

        # Create the Intent Manager
        self.intent = IntentManager(self)

    def get_response(self, user_message):

        # Give the Intent Manager the first chance to handle the message
        response = self.intent.process(user_message)

        # If the Intent Manager handled it, return the result
        if response is not None:
            return response

        # Otherwise continue with the normal AI conversation
        self.conversation.add_user_message(user_message)

        # Detect if the user explicitly requested a tabular response.
        tabular_requests = [
            "tabular", "table", "tabular form", "tabular format", "in table",
            "in a table", "give in a table", "give in tabular", "tabular formate",
            "tabular form" 
        ]
        lower = user_message.lower()

        tabular_requested = any(kw in lower for kw in tabular_requests)

        if tabular_requested:
            # Insert a system-level formatting hint so the model returns a Markdown table
            messages = [
                {
                    "role": "system",
                    "content": (
                        "When the user asks for tabular output, return the information as a Markdown table. "
                        "Wrap the table in triple backticks (```markdown ... ```). Use short headers and keep cells concise. "
                        "If columns are not specified, infer reasonable column names from the content. "
                        "Do not include any extra explanatory text outside the fenced table."
                    )
                }
            ] + self.conversation.get_messages()

            response = self.ai.ask(messages)
        else:
            response = self.ai.ask(
                self.conversation.get_messages()
            )

        # If the user requested a tabular output but the model returned plain text
        # (no fenced markdown table), ask the model to strictly convert the reply
        # into a fenced Markdown table. This is a single post-processing retry.
        if tabular_requested:
            normalized = (response or "").strip()
            if "```" not in normalized or "|" not in normalized:
                convert_messages = [
                    {
                        "role": "system",
                        "content": (
                            "Strictly convert the following assistant reply into a Markdown table only. "
                            "Return only a fenced markdown block (```markdown ... ```). Do not add any text before or after the fenced block. "
                            "Use short headers and keep cells concise. If the reply contains a list of items, make one item per row."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            "Convert this text into a Markdown table (return only the fenced table):\n\n" + normalized
                        )
                    }
                ]

                try:
                    converted = self.ai.ask(convert_messages)
                    if converted and converted.strip():
                        response = converted
                except Exception:
                    # If the conversion fails, keep the original response.
                    pass

        self.conversation.add_assistant_message(response)

        return response