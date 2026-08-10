import sys
import types
import unittest
from unittest.mock import patch

from src.ai_model import AIModel


class AIModelTests(unittest.TestCase):
    def test_fallback_response_when_ollama_is_unavailable(self):
        model = AIModel()
        dummy_ollama = types.SimpleNamespace(chat=lambda *args, **kwargs: (_ for _ in ()).throw(Exception("ollama unavailable")))

        with patch("src.ai_model.importlib.util.find_spec", return_value=object()):
            with patch.dict(sys.modules, {"ollama": dummy_ollama}):
                response = model.ask([{"role": "user", "content": "hello"}])

        self.assertIn("NOVAX", response)
        self.assertIn("hello", response.lower())


if __name__ == "__main__":
    unittest.main()
