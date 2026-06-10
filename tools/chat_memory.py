import json
import time
from pathlib import Path


class ChatMemory:
    def __init__(self, memory_file: str = "uploads/chat_memory.json"):
        self.memory_file = Path(memory_file)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.memory_file.exists():
            self.memory_file.write_text("{}", encoding="utf-8")

    def _load(self):
        try:
            return json.loads(self.memory_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self, data):
        self.memory_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add(self, session_id: str, role: str, content: str):
        data = self._load()
        data.setdefault(session_id, [])
        data[session_id].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        data[session_id] = data[session_id][-30:]
        self._save(data)

    def get(self, session_id: str):
        return self._load().get(session_id, [])

    def clear(self, session_id: str):
        data = self._load()
        data[session_id] = []
        self._save(data)
