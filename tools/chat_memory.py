import json
import re
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

    def find_similar_answer(self, session_id: str, query: str, threshold: float = 0.55):
        messages = self.get(session_id)
        query_tokens = self._tokens(query)
        if not query_tokens:
            return None

        best = None
        best_score = 0.0
        for idx, message in enumerate(messages[:-1]):
            if message.get("role") != "user":
                continue
            next_message = messages[idx + 1]
            if next_message.get("role") != "assistant":
                continue
            answer = (next_message.get("content") or "").strip()
            if not answer or self._is_non_reusable_answer(answer):
                continue

            score = self._similarity(query_tokens, self._tokens(message.get("content", "")))
            if score > best_score:
                best_score = score
                best = {
                    "answer": answer,
                    "matched_query": message.get("content", ""),
                    "similarity": round(score, 3),
                }

        if best and best_score >= threshold:
            return best
        return None

    @staticmethod
    def _is_non_reusable_answer(answer: str) -> bool:
        text = answer.lower()
        blocked_markers = [
            "agent selected.",
            "rag sources:",
            "collected fields:",
            "i need one more detail",
            "slot filling",
            "safety: no product was purchased",
            "explicit user confirmation is required",
            "i could not find a verified answer",
        ]
        return any(marker in text for marker in blocked_markers)

    @staticmethod
    def _tokens(text: str) -> set[str]:
        stopwords = {
            "a", "an", "and", "are", "can", "could", "did", "do", "does",
            "for", "give", "has", "have", "i", "in", "is", "it", "me",
            "of", "on", "please", "plz", "show", "tell", "the", "to",
            "was", "were", "what", "when", "where", "which", "who", "why",
        }
        words = re.findall(r"[a-z0-9]+", text.lower())
        normalized = []
        for word in words:
            if word in stopwords:
                continue
            if word.endswith("s") and len(word) > 4:
                word = word[:-1]
            normalized.append(word)
        return set(normalized)

    @staticmethod
    def _similarity(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        overlap = len(left & right)
        containment = overlap / min(len(left), len(right))
        jaccard = overlap / len(left | right)
        return (containment * 0.7) + (jaccard * 0.3)

    def clear(self, session_id: str):
        data = self._load()
        data[session_id] = []
        self._save(data)
