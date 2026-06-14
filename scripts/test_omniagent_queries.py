import argparse
import json
from pathlib import Path

from agents.general_agent import GeneralAgent

INPUT_FILE = "knowledge_queries.jsonl"
RESULT_FILE = "omniagent_results.jsonl"


def is_successful_answer(answer: str) -> bool:
    if not answer:
        return False
    blocked_markers = [
        "could not verify",
        "could not find a verified answer",
        "try rephrasing",
    ]
    low = answer.lower()
    return not any(marker in low for marker in blocked_markers)


def run_queries(
    input_file: Path = Path(INPUT_FILE),
    result_file: Path = Path(RESULT_FILE),
    limit: int | None = None,
    session_id: str = "knowledge_eval",
) -> dict:
    agent = GeneralAgent()
    total = 0
    answered = 0
    failed = 0

    with input_file.open("r", encoding="utf-8") as handle, result_file.open("w", encoding="utf-8") as out:
        for line in handle:
            if limit is not None and total >= limit:
                break

            item = json.loads(line)
            query = item["query"]

            try:
                result = agent.run(query, session_id=session_id)
                answer = result.get("answer", "")
                ok = is_successful_answer(answer)

                if ok:
                    answered += 1
                else:
                    failed += 1

                out.write(json.dumps({
                    "query": query,
                    "answer": answer,
                    "expected_title": item.get("expected_title", ""),
                    "expected_source": item.get("expected_source", ""),
                    "source_stage": result.get("extra", {}).get("source_stage", ""),
                    "success": ok,
                }, ensure_ascii=False) + "\n")

            except Exception as exc:
                failed += 1
                out.write(json.dumps({
                    "query": query,
                    "expected_title": item.get("expected_title", ""),
                    "error": str(exc),
                    "success": False,
                }, ensure_ascii=False) + "\n")

            total += 1

    return {
        "total": total,
        "answered": answered,
        "failed": failed,
        "accuracy": answered / total if total else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Run generated knowledge queries through OmniAgent.")
    parser.add_argument("--input", type=Path, default=Path(INPUT_FILE))
    parser.add_argument("--output", type=Path, default=Path(RESULT_FILE))
    parser.add_argument("--limit", type=int, help="Limit number of queries for a quick smoke test.")
    parser.add_argument("--session-id", default="knowledge_eval")
    args = parser.parse_args()

    stats = run_queries(
        input_file=args.input,
        result_file=args.output,
        limit=args.limit,
        session_id=args.session_id,
    )

    print("Total:", stats["total"])
    print("Answered:", stats["answered"])
    print("Failed:", stats["failed"])
    print("Accuracy:", stats["accuracy"])


if __name__ == "__main__":
    main()
