import re
import urllib.request
import json
import urllib.parse
from src.memory import MemoryManager


class WeatherIntent:
    DEFAULT_LOCATION = "Chennai"

    def __init__(self, brain=None):
        self.brain = brain
        self.memory = brain.memory if (brain and hasattr(brain, "memory")) else MemoryManager()

    def fetch_live_weather(self, location: str) -> dict | None:
        try:
            encoded_loc = urllib.parse.quote(location)
            url = f"https://wttr.in/{encoded_loc}?format=j1"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "curl/7.68.0"}
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                current = data.get("current_condition", [{}])[0]
                area_info = data.get("nearest_area", [{}])[0]
                area_name = area_info.get("areaName", [{}])[0].get("value") or location
                country = area_info.get("country", [{}])[0].get("value") or ""

                temp_c = current.get("temp_C")
                feels_like_c = current.get("FeelsLikeC")
                humidity = current.get("humidity")
                wind_kmph = current.get("windspeedKmph")
                desc = current.get("weatherDesc", [{}])[0].get("value", "Clear")

                return {
                    "location": f"{area_name}, {country}".strip(", "),
                    "temp_c": temp_c,
                    "feels_like_c": feels_like_c,
                    "humidity": humidity,
                    "wind_kmph": wind_kmph,
                    "desc": desc
                }
        except Exception:
            return None

    def get_memory_location(self, user_id="default_user") -> str | None:
        """
        Check whether the user has stored their location/city in the memory module.
        Checks profile, user, and custom memory categories.
        """
        try:
            mem_mgr = self.brain.memory if (self.brain and hasattr(self.brain, "memory")) else self.memory

            # 1. Check primary location fields in profile and user categories
            for cat in ["profile", "user", "personal"]:
                for field in ["city", "location", "place", "residence", "hometown", "current_city", "home_city"]:
                    val = mem_mgr.get(cat, field, user_id=user_id)
                    if val and str(val).strip() and str(val).strip().lower() not in ["not specified", "none", "null", ""]:
                        return str(val).strip()

            # 2. Search all memories across categories
            all_memories = mem_mgr.load_memory(user_id=user_id)
            priority_keys = ["city", "location", "current_city", "home_city", "hometown", "place", "residence", "live_in", "lives_in", "address"]

            for cat, items in all_memories.items():
                if isinstance(items, dict):
                    for k, v in items.items():
                        val = v.get("value", v) if hasattr(v, "get") and callable(v.get) else getattr(v, "value", str(v))
                        val_str = str(val).strip()
                        k_lower = k.lower().strip()

                        # Exact key or prefixed key match (e.g. 'my city', 'current location', 'home city')
                        for pk in priority_keys:
                            if k_lower == pk or k_lower == f"my {pk}" or k_lower == f"current {pk}" or k_lower == f"home {pk}" or k_lower.endswith(f" {pk}"):
                                if val_str and val_str.lower() not in ["true", "false", "none", "null", "not specified", ""]:
                                    return val_str

                        # Phrase in key like "live in London" or "lives in Paris"
                        if val_str.lower() == "true" or not val_str or val_str.lower() == "false":
                            phrase_match = re.search(r'\b(?:live in|lives in|living in|located in|based in|from|staying in|stay in)\s+([a-zA-Z\s]+)', k_lower)
                            if phrase_match:
                                loc_cand = phrase_match.group(1).strip()
                                words = [w for w in loc_cand.split() if w not in ["the", "a", "an", "now", "currently"]]
                                if words:
                                    return " ".join(words).title()

            # 3. Fallback to profile country if specified
            for cat in ["profile", "user"]:
                country = mem_mgr.get(cat, "country", user_id=user_id)
                if country and str(country).strip() and str(country).strip().lower() not in ["not specified", "none", "null", ""]:
                    return str(country).strip()

        except Exception:
            pass
        return None

    def process(self, user_message, user_id="default_user"):
        message = user_message.lower().strip()

        is_weather_query = any(w in message for w in ["weather", "temperature", "forecast", "climate"])
        if not is_weather_query:
            return None

        # 1. Extract location explicitly mentioned in user's query (e.g. "weather in Tokyo")
        location = None
        loc_match = re.search(r'\b(?:at|in|for|of)\s+([a-zA-Z\s]+)', message)
        if loc_match:
            candidate = loc_match.group(1).strip()
            words = [w for w in candidate.split() if w not in ["the", "weather", "link", "page", "site", "url", "temperature", "today", "now", "current"]]
            if words:
                location = " ".join(words).title()

        # 2. If no location in the current query, check if user has filled location in the Memory Module
        if not location:
            memory_loc = self.get_memory_location(user_id=user_id)
            if memory_loc:
                location = memory_loc

        # 3. If still no location, check conversation history for previously mentioned location
        if not location and self.brain and hasattr(self.brain, "conversation"):
            messages = self.brain.conversation.get_messages(user_id=user_id)
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    content = msg.get("content", "").lower()
                    loc_match_prev = re.search(r'\b(?:at|in|for|of)\s+([a-zA-Z\s]+)', content)
                    if loc_match_prev:
                        candidate = loc_match_prev.group(1).strip()
                        words = [w for w in candidate.split() if w not in ["the", "weather", "link", "page", "site", "url", "temperature", "today", "now", "current"]]
                        if words:
                            location = " ".join(words).title()
                            break

        # 4. Fall back to default location
        target_loc = location or self.DEFAULT_LOCATION
        is_link_query = any(kw in message for kw in ["link", "url", "site", "website", "page"])

        if is_link_query:
            query_str = f"weather in {target_loc}"
            search_url = f"https://www.google.com/search?q={query_str.replace(' ', '+')}"
            return f"Here is the direct weather forecast link for **{target_loc}**:\n\n[{target_loc} Weather Forecast]({search_url})"

        # Attempt to fetch live weather details
        weather_data = self.fetch_live_weather(target_loc)
        if weather_data and weather_data.get("temp_c") is not None:
            loc_display = weather_data["location"]
            temp = weather_data["temp_c"]
            feels = weather_data["feels_like_c"]
            desc = weather_data["desc"]
            humidity = weather_data["humidity"]
            wind = weather_data["wind_kmph"]

            return (
                f"**Live Weather Report — {loc_display}**\n\n"
                f"- **Condition**: {desc}\n"
                f"- **Temperature**: {temp}°C (Feels like {feels}°C)\n"
                f"- **Humidity**: {humidity}%\n"
                f"- **Wind Speed**: {wind} km/h\n"
            )

        # Fallback to forecast link if live fetch timed out
        search_url = f"https://www.google.com/search?q=weather+{target_loc.replace(' ', '+')}"
        return f"Current live weather report for **{target_loc}**:\n\n[{target_loc} Live Weather Forecast]({search_url})"
