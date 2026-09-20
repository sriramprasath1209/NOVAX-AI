import re
import urllib.request
import json
import urllib.parse


class WeatherIntent:

    def __init__(self, brain=None):
        self.brain = brain

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

    def process(self, user_message, user_id="default_user"):
        message = user_message.lower().strip()

        is_weather_query = any(w in message for w in ["weather", "temperature", "forecast", "climate"])
        if not is_weather_query:
            return None

        # Extract location
        location = None
        loc_match = re.search(r'\b(?:at|in|for|of)\s+([a-zA-Z\s]+)', message)
        if loc_match:
            candidate = loc_match.group(1).strip()
            words = [w for w in candidate.split() if w not in ["the", "weather", "link", "page", "site", "url", "temperature", "today", "now", "current"]]
            if words:
                location = " ".join(words).title()

        if not location and self.brain and hasattr(self.brain, "conversation"):
            # Check conversation history for previously mentioned location
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

        target_loc = location or "Chennai"
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
