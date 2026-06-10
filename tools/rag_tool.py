import re
from pathlib import Path
from config import KNOWLEDGE_DIR


class RAGTool:
    def __init__(self, knowledge_dir: str = KNOWLEDGE_DIR):
        self.knowledge_dir = Path(knowledge_dir)

    def search(self, query: str, category: str = "", max_chars: int = 3000):
        root = self.knowledge_dir / category if category else self.knowledge_dir

        if not root.exists():
            return {
                "category": category or "all",
                "context": "No knowledge folder found.",
                "sources": []
            }

        query_words = set(re.findall(r"[a-zA-Z0-9]+", query.lower()))
        results = []

        for file in root.rglob("*.txt"):
            text = file.read_text(encoding="utf-8", errors="ignore")
            words = set(re.findall(r"[a-zA-Z0-9]+", text.lower()))
            score = len(query_words & words)

            if score > 0:
                results.append((score, str(file.relative_to(self.knowledge_dir)), text))

        results.sort(reverse=True, key=lambda x: x[0])

        if not results:
            return {
                "category": category or "all",
                "context": "No strong RAG match found.",
                "sources": []
            }

        context = "\n\n".join(
            f"[Source: {src}]\n{text[:1200]}"
            for _, src, text in results[:5]
        )

        return {
            "category": category or "all",
            "context": context[:max_chars],
            "sources": [src for _, src, _ in results[:5]]
        }
