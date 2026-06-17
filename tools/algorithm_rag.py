import re
from pathlib import Path

from config import KNOWLEDGE_DIR


class AlgorithmRAG:
    def __init__(self, file_path: str | Path = "coding/advanced_algorithms.txt"):
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(KNOWLEDGE_DIR) / path
        self.file_path = path
        self.text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        self.blocks = self._parse_blocks(self.text)

    def search(self, query: str, top_k: int = 3):
        query_tokens = self._tokens(query)
        results = []

        for block in self.blocks:
            haystack = block["text"].lower()
            score = 0

            for token in query_tokens:
                if token in haystack:
                    score += 1

            algorithm = block.get("algorithm", "").lower()
            if algorithm and algorithm in query.lower():
                score += 8

            keywords = block.get("keywords", "").lower()
            for keyword in [item.strip() for item in keywords.split(",") if item.strip()]:
                if keyword in query.lower():
                    score += 5

            if score > 0:
                results.append((score, block))

        results.sort(key=lambda item: item[0], reverse=True)
        return [block["text"] for _, block in results[:top_k]] or ["No matching algorithm found."]

    @staticmethod
    def _parse_blocks(text: str):
        blocks = []
        for raw_block in re.split(r"(?m)^(?=Algorithm:|Problem:)", text):
            raw_block = raw_block.strip()
            if not raw_block or not (raw_block.startswith("Algorithm:") or raw_block.startswith("Problem:")):
                continue

            fields = {}
            lines = raw_block.splitlines()
            first_key, first_value = lines[0].split(":", 1)
            fields[first_key.strip().lower()] = first_value.strip()

            for line in lines[1:]:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                fields[key.strip().lower().replace(" ", "_")] = value.strip()

            if "algorithm" not in fields and "generator_key" in fields:
                fields["algorithm"] = fields["generator_key"]
            elif "algorithm" not in fields and "problem" in fields:
                fields["algorithm"] = fields["problem"]

            block_text = raw_block
            if raw_block.startswith("Problem:") and fields.get("algorithm"):
                block_text = f"Algorithm: {fields['algorithm']}\n" + raw_block
            fields["text"] = block_text

            blocks.append(fields)
        return blocks

    @staticmethod
    def _tokens(text: str):
        return set(re.findall(r"[a-zA-Z0-9_+#-]+", (text or "").lower()))
