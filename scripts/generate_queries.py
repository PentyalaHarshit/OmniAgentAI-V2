import argparse
import json
import random
from pathlib import Path

INPUT_FILE = "chunks.jsonl"
OUTPUT_FILE = "knowledge_queries.jsonl"

QUESTION_TEMPLATES = [
    "What is {title}?",
    "Explain {title}.",
    "Who was {title}?",
    "When did {title} happen?",
    "Why is {title} important?",
    "What are the main facts about {title}?",
    "Give a short summary of {title}.",
    "Compare {title} with related concepts.",
    "What caused {title}?",
    "What were the effects of {title}?",
]


def load_chunks(path: Path):
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} in {path}: {exc}") from exc


def make_queries(chunk: dict, queries_per_chunk: int = 5, rng: random.Random | None = None) -> list[dict]:
    title = chunk.get("title", "").strip()
    text = chunk.get("text", "").strip()

    if not title or len(text) < 100:
        return []

    rng = rng or random
    sample_size = min(queries_per_chunk, len(QUESTION_TEMPLATES))
    queries = []

    for template in rng.sample(QUESTION_TEMPLATES, k=sample_size):
        queries.append({
            "query": template.format(title=title),
            "expected_source": chunk.get("source", ""),
            "expected_title": title,
            "expected_context": text[:1000],
        })

    return queries


def generate_queries(
    input_file: Path = Path(INPUT_FILE),
    output_file: Path = Path(OUTPUT_FILE),
    queries_per_chunk: int = 5,
    limit: int | None = None,
    seed: int = 42,
) -> int:
    rng = random.Random(seed)
    total = 0
    chunks_seen = 0

    with output_file.open("w", encoding="utf-8") as out:
        for chunk in load_chunks(input_file):
            if limit is not None and chunks_seen >= limit:
                break
            chunks_seen += 1

            for query in make_queries(chunk, queries_per_chunk=queries_per_chunk, rng=rng):
                out.write(json.dumps(query, ensure_ascii=False) + "\n")
                total += 1

    return total


def main():
    parser = argparse.ArgumentParser(description="Generate OmniAgent evaluation queries from chunk JSONL.")
    parser.add_argument("--input", type=Path, default=Path(INPUT_FILE))
    parser.add_argument("--output", type=Path, default=Path(OUTPUT_FILE))
    parser.add_argument("--queries-per-chunk", type=int, default=5)
    parser.add_argument("--limit", type=int, help="Limit number of chunks for a quick smoke test.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    total = generate_queries(
        input_file=args.input,
        output_file=args.output,
        queries_per_chunk=args.queries_per_chunk,
        limit=args.limit,
        seed=args.seed,
    )
    print(f"Generated {total} queries")


if __name__ == "__main__":
    main()
