class MemoryIntent:

    def __init__(self, brain):
        self.brain = brain

    def process(self, user_message, user_id="default_user"):
        message = user_message.lower().strip()

        # 1. "Remember my name is <name>"
        if message.startswith("remember my name is"):
            name = user_message[len("remember my name is"):].strip()
            if not name:
                return "Please tell me the name you want me to remember."

            self.brain.memory.set("profile", "name", name, user_id=user_id, source="USER")
            self.brain.memory.set("user", "name", name, user_id=user_id, source="USER")
            return f"I'll remember that your name is {name}."

        # 2. "Remember that <key> is <value>"
        elif message.startswith("remember that "):
            content = user_message[len("remember that "):].strip()
            if " is " in content:
                parts = content.split(" is ", 1)
                k = parts[0].strip()
                v = parts[1].strip()
                if k and v:
                    # Assign category based on key hints
                    cat = "custom"
                    k_lower = k.lower()
                    if "skill" in k_lower or "language" in k_lower or "tool" in k_lower:
                        cat = "skills"
                    elif "goal" in k_lower:
                        cat = "goals"
                    elif "interest" in k_lower or "hobby" in k_lower or "like" in k_lower:
                        cat = "interests"
                    elif "education" in k_lower or "school" in k_lower or "college" in k_lower or "degree" in k_lower:
                        cat = "education"
                    elif "job" in k_lower or "role" in k_lower or "work" in k_lower:
                        cat = "career"

                    self.brain.memory.set(cat, k, v, user_id=user_id, source="USER")
                    return f"I've saved that memory: **{k}** = *{v}* in your Memory Center."

            # Single phrase memory
            if content:
                self.brain.memory.set("custom", content, "true", user_id=user_id, source="USER")
                return f"I've added to your Personal Memory: *\"{content}\"*."

        # 3. "Forget my name"
        elif message in ["forget my name", "forget my name."]:
            self.brain.memory.delete("profile", "name", user_id=user_id)
            self.brain.memory.delete("user", "name", user_id=user_id)
            return "I've forgotten your name."

        # 4. "Forget that <item>"
        elif message.startswith("forget that "):
            item = user_message[len("forget that "):].strip()
            memories = self.brain.memory.load_memory(user_id=user_id)
            deleted_any = False
            for cat, items in memories.items():
                for k in list(items.keys()):
                    if item.lower() in k.lower() or item.lower() in str(items[k].get("value", "")).lower():
                        self.brain.memory.delete(cat, k, user_id=user_id)
                        deleted_any = True
            if deleted_any:
                return f"I've removed memories matching *\"{item}\"*."
            return f"I couldn't find any memory matching *\"{item}\"*."

        # 5. "Show me what you remember" / "What do you remember about me"
        elif any(phrase in message for phrase in ["what do you remember", "show me what you remember", "show my memories", "view my memories"]):
            memories = self.brain.memory.load_memory(user_id=user_id)
            total = sum(len(items) for items in memories.values())
            if total == 0:
                return "I don't have any saved personal memories for you yet. You can personalize NOVAX in the Memory tab!"

            lines = [f"Here is what I remember about you ({total} item{'s' if total != 1 else ''}):\n"]
            for cat, items in memories.items():
                if items:
                    lines.append(f"**{cat.upper()}**:")
                    for k, item_data in items.items():
                        v = item_data.get("value", "") if isinstance(item_data, dict) else item_data
                        lines.append(f"• {k}: {v}")
                    lines.append("")
            return "\n".join(lines).strip()

        # 6. "Delete all my memories" / "Clear all my memories"
        elif message in ["delete all my memories", "clear all my memories", "forget everything", "delete all memories"]:
            self.brain.memory.clear_all(user_id=user_id)
            return "All your personal memories have been cleared from NOVAX."

        return None