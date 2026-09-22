import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from src.db import Database
from src import auth
import src.db
import src.brain
import src.memory
import src.conversation
from src.brain import Brain
from src.memory import MemoryManager


class TestWeatherMemoryIntegration(unittest.TestCase):

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()

        self.test_db = Database(self.db_path)
        auth.db = self.test_db
        src.db.db = self.test_db
        src.brain.db = self.test_db
        src.memory.db = self.test_db
        src.conversation.db = self.test_db

        self.brain = Brain()
        self.brain.memory = MemoryManager()
        self.user, _ = auth.register_user("weatheruser@example.com", "pass12345", "Weather User")
        self.user_id = self.user["id"]

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    @patch("urllib.request.urlopen")
    def test_weather_fallback_to_default_when_no_memory(self, mock_urlopen):
        fake_weather_json = b'''{
            "current_condition": [
                {
                    "temp_C": "32",
                    "weatherDesc": [{"value": "Sunny"}],
                    "humidity": "70",
                    "FeelsLikeC": "38",
                    "windspeedKmph": "10"
                }
            ],
            "nearest_area": [
                {
                    "areaName": [{"value": "Chennai"}],
                    "country": [{"value": "India"}]
                }
            ]
        }'''
        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_weather_json
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # User asks without location and has NO memory location
        response = self.brain.intent.process("what is the weather today?", user_id=self.user_id)
        self.assertIsNotNone(response)
        self.assertIn("Live Weather Report — Chennai", response)
        self.assertIn("32°C", response)

    @patch("urllib.request.urlopen")
    def test_weather_uses_profile_city_from_memory(self, mock_urlopen):
        # Set user city in profile memory
        self.test_db.set_memory(self.user_id, "profile", "city", "San Francisco", source="USER")

        fake_weather_json = b'''{
            "current_condition": [
                {
                    "temp_C": "18",
                    "weatherDesc": [{"value": "Foggy"}],
                    "humidity": "80",
                    "FeelsLikeC": "18",
                    "windspeedKmph": "15"
                }
            ],
            "nearest_area": [
                {
                    "areaName": [{"value": "San Francisco"}],
                    "country": [{"value": "United States"}]
                }
            ]
        }'''
        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_weather_json
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # User asks for weather without specifying a city
        response = self.brain.intent.process("tell me the current weather", user_id=self.user_id)
        self.assertIsNotNone(response)
        self.assertIn("Live Weather Report — San Francisco", response)
        self.assertIn("Foggy", response)
        self.assertIn("18°C", response)

    @patch("urllib.request.urlopen")
    def test_weather_uses_custom_memory_location(self, mock_urlopen):
        # Set user location in custom memory
        self.test_db.set_memory(self.user_id, "custom", "my location", "Seattle", source="USER")

        fake_weather_json = b'''{
            "current_condition": [
                {
                    "temp_C": "12",
                    "weatherDesc": [{"value": "Light Rain"}],
                    "humidity": "85",
                    "FeelsLikeC": "11",
                    "windspeedKmph": "8"
                }
            ],
            "nearest_area": [
                {
                    "areaName": [{"value": "Seattle"}],
                    "country": [{"value": "United States"}]
                }
            ]
        }'''
        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_weather_json
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # User asks for weather
        response = self.brain.intent.process("what is the temperature outside?", user_id=self.user_id)
        self.assertIsNotNone(response)
        self.assertIn("Live Weather Report — Seattle", response)
        self.assertIn("Light Rain", response)

    def test_weather_link_uses_memory_location(self):
        self.test_db.set_memory(self.user_id, "profile", "city", "London", source="USER")

        response = self.brain.intent.process("can you give me the weather forecast link", user_id=self.user_id)
        self.assertIsNotNone(response)
        self.assertIn("London Weather Forecast", response)
        self.assertIn("https://www.google.com/search?q=weather+in+London", response)

    @patch("urllib.request.urlopen")
    def test_explicit_location_overrides_memory_location(self, mock_urlopen):
        # User has Paris in memory
        self.test_db.set_memory(self.user_id, "profile", "city", "Paris", source="USER")

        fake_weather_json = b'''{
            "current_condition": [
                {
                    "temp_C": "28",
                    "weatherDesc": [{"value": "Clear"}],
                    "humidity": "50",
                    "FeelsLikeC": "28",
                    "windspeedKmph": "5"
                }
            ],
            "nearest_area": [
                {
                    "areaName": [{"value": "Tokyo"}],
                    "country": [{"value": "Japan"}]
                }
            ]
        }'''
        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_weather_json
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # But explicitly asks for Tokyo
        response = self.brain.intent.process("what is the weather in Tokyo?", user_id=self.user_id)
        self.assertIsNotNone(response)
        self.assertIn("Live Weather Report — Tokyo", response)

    @patch("urllib.request.urlopen")
    def test_remember_city_intent_flow(self, mock_urlopen):
        fake_weather_json = b'''{
            "current_condition": [
                {
                    "temp_C": "24",
                    "weatherDesc": [{"value": "Partly Cloudy"}],
                    "humidity": "60",
                    "FeelsLikeC": "25",
                    "windspeedKmph": "12"
                }
            ],
            "nearest_area": [
                {
                    "areaName": [{"value": "Berlin"}],
                    "country": [{"value": "Germany"}]
                }
            ]
        }'''
        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_weather_json
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # 1. User tells NOVAX to remember city
        mem_reply = self.brain.intent.process("remember my city is Berlin", user_id=self.user_id)
        self.assertIn("I'll remember that your city is **Berlin**", mem_reply)

        # 2. User asks for weather without specifying Berlin
        weather_reply = self.brain.intent.process("weather forecast today", user_id=self.user_id)
        self.assertIn("Live Weather Report — Berlin", weather_reply)
        self.assertIn("Partly Cloudy", weather_reply)


if __name__ == "__main__":
    unittest.main()
