import json
import re
import sqlite3
import zipfile
from pathlib import Path


def normalize_fact_query(query: str) -> str:
    q = query.lower().strip()
    q = q.replace("?", "")
    q = q.replace("-", " ")
    q = re.sub(r"[^a-z0-9\s+.#]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q


class HugeGeneralFacts:
    """
    SQLite-backed lookup for large JSONL fact files.

    Expected JSONL fields:
    {"query": "...", "answer": "...", "category": "...", "source": "..."}
    """

    def __init__(
        self,
        db_path: str = "knowledge/general_facts.sqlite",
        jsonl_path: str = "knowledge/general_facts_seed.jsonl",
    ):
        self.db_path = Path(db_path)
        self.jsonl_path = Path(jsonl_path)

    def lookup(self, query: str) -> str:
        key = normalize_fact_query(query)
        if not key:
            return ""

        keys = self.query_variants(key)

        db_answer = self._lookup_sqlite(keys)
        if db_answer and not self.is_placeholder_answer(db_answer):
            return db_answer

        if self.jsonl_path.exists() and self.jsonl_path.stat().st_size < 5_000_000:
            return self._lookup_small_jsonl(keys)

        return ""

    @staticmethod
    def is_placeholder_answer(answer: str) -> bool:
        text = re.sub(r"\s+", " ", (answer or "").strip().lower())
        return bool(re.search(
            r"\bis important because (it|this) is a key topic in .+ "
            r"and connects to many real-world systems, events, or ideas\.?$",
            text,
        ))

    @staticmethod
    def query_variants(key: str) -> list[str]:
        variants = [key]

        article_stripped = re.sub(r"\b(a|an|the)\b", " ", key)
        article_stripped = re.sub(r"\s+", " ", article_stripped).strip()
        variants.append(article_stripped)

        replacements = [
            (r"^tell me about (.+)$", r"what is \1"),
            (r"^define (.+)$", r"what is \1"),
            (r"^explain what is (.+)$", r"what is \1"),
            (r"^who is (.+)$", r"who was \1"),
            (r"^who was the (.+)$", r"who was \1"),
            (r"^what are (.+)$", r"what is \1"),
            (r"^give me a short summary of (.+)$", r"give a short summary of \1"),
            (r"^give me a short summary of (.+)$", r"what is \1"),
            (r"^give a short summary of (.+)$", r"what is \1"),
            (r"^explain (.+)$", r"what is \1"),
        ]
        for pattern, replacement in replacements:
            if re.search(pattern, key):
                variants.append(re.sub(pattern, replacement, key))
            if re.search(pattern, article_stripped):
                variants.append(re.sub(pattern, replacement, article_stripped))

        return list(dict.fromkeys(v for v in variants if v))

    def _lookup_sqlite(self, keys: list[str]) -> str:
        if not self.db_path.exists():
            return ""
        try:
            with sqlite3.connect(self.db_path) as conn:
                placeholders = ",".join("?" for _ in keys)
                row = conn.execute(
                    f"SELECT answer FROM facts WHERE normalized_query IN ({placeholders}) LIMIT 1",
                    keys,
                ).fetchone()
                return row[0] if row else ""
        except sqlite3.Error:
            return ""

    def _lookup_small_jsonl(self, keys: list[str]) -> str:
        try:
            with self.jsonl_path.open("r", encoding="utf-8-sig") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    if normalize_fact_query(item.get("query", "")) in keys:
                        answer = item.get("answer", "")
                        if not self.is_placeholder_answer(answer):
                            return answer
        except (OSError, json.JSONDecodeError):
            return ""
        return ""

    @classmethod
    def build_index(
        cls,
        jsonl_path: str | Path,
        db_path: str | Path = "knowledge/general_facts.sqlite",
        batch_size: int = 5000,
        zip_entry: str = "",
        limit: int | None = None,
    ) -> dict:
        jsonl_path = Path(jsonl_path)
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        total = 0
        skipped = 0
        batch = []

        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    normalized_query TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    category TEXT,
                    source TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)")

            for item in cls.iter_jsonl_items(jsonl_path, zip_entry=zip_entry):
                if limit is not None and total + len(batch) >= limit:
                    break
                query = item.get("query", "").strip()
                answer = item.get("answer", "").strip()
                normalized = normalize_fact_query(query)
                if not normalized or not answer:
                    skipped += 1
                    continue

                batch.append((
                    normalized,
                    query,
                    answer,
                    item.get("category", ""),
                    item.get("source", ""),
                ))

                if len(batch) >= batch_size:
                    conn.executemany(
                        """
                        INSERT OR REPLACE INTO facts
                        (normalized_query, query, answer, category, source)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        batch,
                    )
                    total += len(batch)
                    batch = []

            if batch:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO facts
                    (normalized_query, query, answer, category, source)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    batch,
                )
                total += len(batch)

        return {"indexed": total, "skipped": skipped, "db_path": str(db_path)}

    @staticmethod
    def iter_jsonl_items(path: Path, zip_entry: str = ""):
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                entry_name = zip_entry or next(
                    (
                        name for name in archive.namelist()
                        if name.lower().endswith(".jsonl")
                    ),
                    "",
                )
                if not entry_name:
                    raise ValueError(f"No .jsonl entry found in zip: {path}")
                with archive.open(entry_name) as raw:
                    for line in raw:
                        line = line.decode("utf-8-sig").strip()
                        if not line:
                            continue
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue
            return

        with path.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
