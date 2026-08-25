import re

class WeatherIntent:

    def __init__(self, brain):
        self.brain = brain

    def process(self, user_message, user_id="default_user"):
        message = user_message.lower().strip()

        # Check if the user is asking for a weather link
        is_weather_query = "weather" in message
        is_link_query = any(kw in message for kw in ["link", "url", "site", "website", "page"])

        if is_weather_query and is_link_query:
            # Check for location in current message or previous messages
            location = None
            
            # Extract location after "at", "in", "for", or "of"
            loc_match = re.search(r'\b(?:at|in|for|of)\s+([a-zA-Z\s]+)', message)
            if loc_match:
                candidate = loc_match.group(1).strip()
                words = [w for w in candidate.split() if w not in ["the", "weather", "link", "page", "site", "url"]]
                if words:
                    location = " ".join(words).title()

            # If no location in current message, look back at conversation history
            if not location:
                messages = self.brain.conversation.get_messages(user_id=user_id)
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        content = msg.get("content", "").lower()
                        loc_match_prev = re.search(r'\b(?:at|in|for|of)\s+([a-zA-Z\s]+)', content)
                        if loc_match_prev:
                            candidate = loc_match_prev.group(1).strip()
                            words = [w for w in candidate.split() if w not in ["the", "weather", "link", "page", "site", "url"]]
                            if words:
                                location = " ".join(words).title()
                                break

            target_loc = location or "Current Location"
            query_str = f"weather in {target_loc}" if location else "weather forecast"
            search_url = f"https://www.google.com/search?q={query_str.replace(' ', '+')}"

            return f"Here is the direct weather forecast link for **{target_loc}**:\n\n[{target_loc} Weather Forecast]({search_url})"

        return None
