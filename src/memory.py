import json
from pathlib import Path


class MemoryManager:

    def __init__(self):
        self.memory_file = Path(__file__).resolve().parent.parent / "data" / "memory.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

    def load_memory(self):
        if not self.memory_file.exists():
            return {}

        with open(self.memory_file, "r") as file:
            return json.load(file)

    def save_memory(self, memory):
        with open(self.memory_file, "w") as file:
            json.dump(memory, file, indent=4)

    def get(self, category, key):
        memory = self.load_memory()
        return memory.get(category, {}).get(key)

    def set(self, category, key, value):
        memory = self.load_memory()

        if category not in memory:
            memory[category] = {}

        memory[category][key] = value

        self.save_memory(memory)

    def delete(self, category, key):
        memory = self.load_memory()

        if category in memory and key in memory[category]:
            del memory[category][key]

        self.save_memory(memory)