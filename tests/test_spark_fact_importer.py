from scripts.import_general_facts_spark import write_rows_to_sqlite
from tools.huge_general_facts import HugeGeneralFacts


def test_write_rows_to_sqlite_accepts_spark_like_rows(tmp_path):
    class RowLike(dict):
        pass

    db = tmp_path / "spark_facts.sqlite"
    rows = [
        RowLike({
            "normalized_query": "what is cpu",
            "query": "what is cpu",
            "answer": "A CPU executes instructions.",
            "category": "technology",
            "source": "spark_test",
        }),
        RowLike({
            "normalized_query": "what is gpu",
            "query": "what is gpu",
            "answer": "A GPU handles parallel computation.",
            "category": "technology",
            "source": "spark_test",
        }),
    ]

    indexed = write_rows_to_sqlite(rows, db, batch_size=1)
    facts = HugeGeneralFacts(db_path=str(db), jsonl_path=str(tmp_path / "missing.jsonl"))

    assert indexed == 2
    assert facts.lookup("what is a cpu") == "A CPU executes instructions."
    assert facts.lookup("define gpu") == "A GPU handles parallel computation."
