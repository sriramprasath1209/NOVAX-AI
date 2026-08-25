from src.ai_model import AIModel
from src.conversation import Conversation
from src.memory import MemoryManager
from src.intent import IntentManager
from src.search_engine import SearchEngine


class Brain:

    def __init__(self):
        self.ai = AIModel()
        self.conversation = Conversation()
        self.memory = MemoryManager()
        self.search_engine = SearchEngine()

        # Create the Intent Manager
        self.intent = IntentManager(self)

    def get_response(self, user_message, user_id="default_user", user_name=None):

        # Fetch stored user name if not provided
        if not user_name:
            user_name = self.memory.get("user", "name", user_id=user_id) or "User"

        # Give the Intent Manager the first chance to handle the message
        response = self.intent.process(user_message, user_id=user_id)

        # If the Intent Manager handled it, return the result
        if response is not None:
            return response

        # Otherwise continue with the normal AI conversation
        self.conversation.add_user_message(user_message, user_id=user_id)

        # Detect if the user explicitly requested a tabular response.
        tabular_requests = [
            "tabular", "table", "tabular form", "tabular format", "in table",
            "in a table", "give in a table", "give in tabular", "tabular formate",
            "tabular form" 
        ]
        lower = user_message.lower()

        tabular_requested = any(kw in lower for kw in tabular_requests)

        # Build authenticated user context system message
        user_context_message = {
            "role": "system",
            "content": (
                f"[Authenticated User Context]\n"
                f"Current User Name: {user_name}\n"
                f"User ID: {user_id}\n\n"
                f"Product Identity: You are NOVAX-AI, an intelligent personal AI agent created by Sriram Prasath. "
                f"You are currently assisting {user_name}. If asked 'who created NOVAX' or 'who made you', answer Sriram Prasath. "
                f"If asked 'what is my name' or 'who am I', answer that their name is {user_name}."
            )
        }

        # Live Web Search & Real-Time News enrichment
        search_context_message = None
        is_news_query = any(kw in lower for kw in ["news", "latest", "update", "updates", "current events", "what happened", "today news"])
        
        if is_news_query:
            news_data = self.search_engine.fetch_live_news(user_message)
            if news_data:
                search_context_message = {
                    "role": "system",
                    "content": (
                        f"[Live Real-Time News Feed - Just In]\n"
                        f"{news_data}\n\n"
                        f"Instructions: You HAVE full access to live real-time news. Use the live headlines and timestamps above to summarize and answer the user's request about the latest news clearly and accurately. Never claim you don't have access to current news."
                    )
                }
        else:
            should_search = any(
                word in lower for word in [
                    "who is", "who was", "what is", "where is", "tell me about",
                    "cm", "minister", "actor", "president", "chief minister", "details of", "information", "vijay"
                ]
            )

            if should_search:
                search_results = self.search_engine.search_wikipedia(user_message)
                if search_results:
                    primary = search_results[0]
                    search_context_message = {
                        "role": "system",
                        "content": (
                            f"[Verified Live Information]\n"
                            f"Title: {primary.get('title')}\n"
                            f"Fact Summary: {primary.get('extract')}\n\n"
                            f"Instructions: Use the verified live information above to provide 100% accurate details in plain text. Do not include any images or photo tags."
                        )
                    }

        user_messages = self.conversation.get_messages(user_id=user_id)
        messages_to_send = [user_context_message] + user_messages
        if search_context_message:
            messages_to_send = [search_context_message] + messages_to_send

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
            ] + messages_to_send

            response = self.ai.ask(messages)
        else:
            response = self.ai.ask(messages_to_send)

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

        self.conversation.add_assistant_message(response, user_id=user_id)

        return response