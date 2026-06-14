import argparse
import sqlite3
from pathlib import Path


def build_spark_index(
    input_path: Path,
    db_path: Path = Path("knowledge/general_facts.sqlite"),
    batch_size: int = 20000,
    limit: int | None = None,
    master: str = "local[*]",
    app_name: str = "OmniAgentMillionFactsImport",
) -> dict:
    if input_path.suffix.lower() == ".zip":
        raise ValueError(
            "PySpark cannot read this zip JSONL directly. "
            "Use scripts/import_general_facts.py --zip-entry, or extract the JSONL first."
        )

    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F
    except ImportError as exc:
        raise RuntimeError(
            "PySpark is not installed. Install it with: pip install pyspark"
        ) from exc

    db_path.parent.mkdir(parents=True, exist_ok=True)

    spark = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
        .getOrCreate()
    )

    try:
        df = spark.read.json(str(input_path))
        required = {"query", "answer"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Input JSONL is missing required columns: {sorted(missing)}")

        category_col = F.col("category") if "category" in df.columns else F.lit("")
        source_col = F.col("source") if "source" in df.columns else F.lit("")

        normalized = F.lower(F.trim(F.col("query")))
        normalized = F.regexp_replace(normalized, r"\?", "")
        normalized = F.regexp_replace(normalized, r"-", " ")
        normalized = F.regexp_replace(normalized, r"[^a-z0-9\s+.#]", " ")
        normalized = F.trim(F.regexp_replace(normalized, r"\s+", " "))

        facts = (
            df.select(
                normalized.alias("normalized_query"),
                F.trim(F.col("query")).alias("query"),
                F.trim(F.col("answer")).alias("answer"),
                F.coalesce(category_col.cast("string"), F.lit("")).alias("category"),
                F.coalesce(source_col.cast("string"), F.lit("")).alias("source"),
            )
            .where(F.col("normalized_query") != "")
            .where(F.col("answer") != "")
            .dropDuplicates(["normalized_query"])
        )

        if limit is not None:
            facts = facts.limit(limit)

        indexed = write_rows_to_sqlite(facts.toLocalIterator(), db_path, batch_size)
        return {"indexed": indexed, "db_path": str(db_path)}
    finally:
        spark.stop()


def write_rows_to_sqlite(rows, db_path: Path, batch_size: int) -> int:
    total = 0
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

        for row in rows:
            batch.append((
                row["normalized_query"],
                row["query"],
                row["answer"],
                row["category"],
                row["source"],
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

    return total


def main():
    parser = argparse.ArgumentParser(
        description="Use PySpark to normalize a large fact JSONL file and index it into SQLite."
    )
    parser.add_argument("jsonl", type=Path, help="Path to million-fact JSONL file.")
    parser.add_argument("--db", type=Path, default=Path("knowledge/general_facts.sqlite"))
    parser.add_argument("--batch-size", type=int, default=20000)
    parser.add_argument("--limit", type=int, help="Import only the first N normalized facts for a smoke test.")
    parser.add_argument("--master", default="local[*]", help="Spark master, e.g. local[*] or spark://host:7077.")
    args = parser.parse_args()

    stats = build_spark_index(
        input_path=args.jsonl,
        db_path=args.db,
        batch_size=args.batch_size,
        limit=args.limit,
        master=args.master,
    )

    print("Indexed:", stats["indexed"])
    print("DB:", stats["db_path"])


if __name__ == "__main__":
    main()
