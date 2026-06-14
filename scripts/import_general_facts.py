import argparse
from pathlib import Path

from tools.huge_general_facts import HugeGeneralFacts


def main():
    parser = argparse.ArgumentParser(description="Index JSONL general facts into SQLite for OmniAgent.")
    parser.add_argument("jsonl", type=Path, help="Path to fact JSONL file, or a zip containing a JSONL file.")
    parser.add_argument("--db", type=Path, default=Path("knowledge/general_facts.sqlite"))
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--zip-entry", default="", help="JSONL entry name inside a zip file.")
    parser.add_argument("--limit", type=int, help="Import only the first N valid facts for a smoke test.")
    args = parser.parse_args()

    stats = HugeGeneralFacts.build_index(
        jsonl_path=args.jsonl,
        db_path=args.db,
        batch_size=args.batch_size,
        zip_entry=args.zip_entry,
        limit=args.limit,
    )
    print("Indexed:", stats["indexed"])
    print("Skipped:", stats["skipped"])
    print("DB:", stats["db_path"])


if __name__ == "__main__":
    main()
